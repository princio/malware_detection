import os
import pandas as pd
import sqlite3
import hashlib
import subprocess
from datetime import datetime
import sys
import psycopg2


def hash_(pcap_path):
    BUF_SIZE = 65536 * 10
    sha256 = hashlib.sha256()
    with open(pcap_path, "rb") as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            sha256.update(data)
    return sha256.hexdigest()


def pcap2postgres(pcap_path, infected=False, redo=False):
    if not os.path.exists(pcap_path):
        print("File not exists.")
        return False

    dns_parser = "/home/princio/Desktop/dns_parse/bin/dns_parse"
    pcap_name = os.path.basename(pcap_path)

    print("Pcap: %s" % pcap_path)
    pcap_hash = hash_(pcap_path)
    print("Hashed.")

    db = psycopg2.connect("host=localhost dbname=dns user=postgres password=postgres")
    cur = db.cursor()

    try:
        to_do = True
        cur.execute("""SELECT id, qr FROM pcap WHERE hash = %s""", [pcap_hash])
        pcap_id = cur.fetchone()

        if pcap_id is not None:
            message_count = pcap_id[1]
            pcap_id = pcap_id[0]
            cur.execute(
                """SELECT COUNT(id) FROM message WHERE pcap_id = %s""", [pcap_id]
            )
            message_inserted = cur.fetchone()[0]

            if message_count != message_inserted:
                print(
                    "Mismatch for <%s>:\n#####%d != %d"
                    % (pcap_path, message_count, message_inserted)
                )
                cur.execute("""DELETE FROM message WHERE pcap_id = %s""", [pcap_id])
                cur.execute("""DELETE FROM pcap WHERE id = %s""", [pcap_id])
                to_do = True
            else:
                to_do = redo

        if not to_do:
            return True

        print("Parsing...")
        if False:
            ret = subprocess.run([dns_parser, "-ndcS", pcap_path], capture_output=True)
            if ret.returncode != 0:
                raise Exception("Error during parsing:\n%s" % ret.stderr)
        else:
            fields = [
                "dns.response_in",
                "frame.number",
                "frame.time_epoch",
                "ip.src",
                "ip.dst",
                "udp.srcport",
                "udp.dstport",
                "dns.id",
                "dns.qry.name",
                "dns.flags.response",
                "dns.flags.rcode",
                "dns.qry.type",
                "dns.a",
                "dns.response_to",
                "dns.retransmission",
                "dns.retransmit_request",
                "dns.retransmit_request_in",
                "dns.retransmit_response",
                "dns.retransmit_response_in",
            ]

            cmd_fields = []
            for f in fields:
                cmd_fields.append("-e")
                cmd_fields.append(f)

            print(' '.join([
                        "tshark",
                        "-n",
                        "-r",
                        pcap_path,
                        "-Y",
                        "dns",  # && !_ws.malformed && !icmp',
                        "-T",
                        "fields",
                    ]
                    + cmd_fields
                    + ["-Eseparator=," "-Equote=d", "-Eheader=y"]))

            with open("/tmp/dnsparse.csv", "w") as outfile:
                ret = subprocess.run(
                    [
                        "tshark",
                        # "-n",
                        "-r",
                        pcap_path,
                        "-Y",
                        "dns",  # && !_ws.malformed && !icmp',
                        "-T",
                        "fields",
                    ]
                    + cmd_fields
                    + ["-Eseparator=,", "-Equote=d",  "-Eheader=y"],
                    stdout=outfile,
                )

        print("Reading...")
        df = pd.read_csv("/tmp/dnsparse.csv", index_col=False)

        print(df)

        exit(1)

        print("Inserting pcap...")
        delta = datetime.fromtimestamp(df["time"].iloc[-1]) - datetime.fromtimestamp(
            df["time"].iloc[0]
        )
        pcap_days = float(f"{delta.days}.{int(delta.seconds/3600/0.24)}")

        qr = df.shape[0]
        q = df[df.qr == "q"].shape[0]
        r = qr - q
        u = df.dn.drop_duplicates().shape[0]
        cur.execute(
            """INSERT INTO pcap (name, hash, infected, qr, q, r, "unique", unique_norm, days) VALUES
                                        (%s,%s,%s::boolean,%s::bigint,%s::bigint,%s::bigint,%s::bigint,%s::real, %s::integer)
                                        RETURNING id""",
            [pcap_name, pcap_hash, infected, qr, q, r, u, u / qr, pcap_days],
        )
        pcap_id = cur.fetchone()[0]

        df_dn = pd.read_sql("SELECT dn, id FROM dn", db).set_index("dn")
        dict_dn = {str(idx): row["id"] for idx, row in df_dn.iterrows()}

        print("Inserting DNs...")
        inserts = []
        df_udn = df["dn"].copy().drop_duplicates()
        df_udn["id"] = -1
        inserts = []
        for _, row in df_udn.iterrows():
            if row["dn"] not in dict_dn:
                inserts.append([row["dn"]])
        if len(inserts) > 0:
            cur.executemany(
                """INSERT INTO "dn" ("dn") VALUES (%s,%s);""", inserts
            )
            db.commit()
        print("Inserted %d DNs." % len(inserts))

        df_dn = pd.read_sql("SELECT dn, id FROM dn", db)

        dff = df.merge(df_dn, left_on="dn", right_on="dn")
        dff["dn"] = dff["id"]
        dff = dff.drop(columns=["id", "bdn"]).rename(columns={"dn": "dn_id"})
        dff["qr"] = dff["qr"].apply(lambda x: x == "r")

        dff.AA = dff.AA.where(dff.AA == 1, True)
        dff.AA = dff.AA.where(dff.AA == 0, False)
        dff = dff.where(pd.notnull(dff), None)

        fields = {
            "pcap_id": "%s",
            "fn": "%s::bigint",
            "time_": "%s::real",
            "server": "%s",
            "port": "%s",
            "dns_id": "%s::bigint",
            "is_response": "%s::boolean",
            "rcode": "%s::integer",
            # "dn_id": "%s::bigint",
            "qcode": "%s::integer",
            "answer": "%s::text",
        }
        print("Inserting messages...")
        sql = (
            'INSERT INTO "message" ('
            + '"%s"' % '","'.join(list(fields.keys()))
            + ") VALUES ("
            + ", ".join(list(fields.values()))
            + ");"
        )
        dff.insert(0, "pcap_id", pcap_id)
        cur.executemany(sql, dff.values)

        db.commit()
        print("Done.")
    except Exception as e:
        print(e)
        db.close()
        raise e
        return False

    db.close()
    return True


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("No pcap path passed.")
        exit(1)

    pcap_path = sys.argv[1]
    redo = bool(sys.argv[1])

    print(redo)
    exit(pcap2postgres(pcap_path, redo=redo))

    pass
