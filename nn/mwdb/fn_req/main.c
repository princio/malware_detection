#include <libpq-fe.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum {
  MESSAGES_ID = 0,
  MESSAGES_PCAP_ID,
  MESSAGES_FN,
  MESSAGES_TIME_S,
  MESSAGES_DNS_ID,
  MESSAGES_IS_RESPONSE,
  MESSAGES_RCODE,
  MESSAGES_DN_ID,
  MESSAGES_QCODE,
  MESSAGES_FN_REQ,
  MESSAGES_FN_REQ2
};

enum {
  PCAP_ID,
  PCAP_NAME,
  PCAP_MALWARE_ID,
  PCAP_HASH,
  PCAP_INFECTED,
  PCAP_QR,
  PCAP_Q,
  PCAP_R,
  PCAP_UNIQUE,
  PCAP_UNIQUE_NORM,
  PCAP_DAYS
};

PGconn *conn;

void do_exit(PGconn *conn) {

  PQfinish(conn);
  exit(1);
}

PGresult * select(const char *query) {

  PGresult *res = PQexec(conn, query);

  if (PQresultStatus(res) != PGRES_TUPLES_OK) {
    printf("Select failed: %s", PQresultErrorMessage(res));
    PQclear(res);
    do_exit(conn);
  }

  return res;
}

PGresult * update(const char *query) {

  PGresult *res = PQexec(conn, query);

  if (PQresultStatus(res) != PGRES_COMMAND_OK) {
    printf("Update failed: %s", PQresultErrorMessage(res));
    PQclear(res);
    do_exit(conn);
  }

  PQclear(res);

  return NULL;
}

int main() {
  setvbuf(stdout, NULL, _IONBF, 0);
  conn =
      PQconnectdb("host=localhost dbname=dns user=postgres password=postgres");

  if (PQstatus(conn) == CONNECTION_BAD) {

    fprintf(stderr, "Connection to database failed: %s\n",
            PQerrorMessage(conn));
    do_exit(conn);
  }

  PGresult *pcaps = select("SELECT * FROM PCAP ORDER BY qr");

  int pcap_num = PQntuples(pcaps);

  printf("Preparing %d\n", pcap_num);
  for (int i = 0; i < pcap_num; ++i) {

    int LEN = 120;
    int pcap_id;
    char query_messages[LEN];

    printf("%s %s\n", PQgetvalue(pcaps, i, PCAP_ID),
           PQgetvalue(pcaps, i, PCAP_QR));

    pcap_id = atoi(PQgetvalue(pcaps, i, 0));

    snprintf(query_messages, LEN,
             "SELECT ID, IS_RESPONSE::int FROM MESSAGES_%d WHERE "
             "FN_REQ IS NULL ORDER BY FN",
             pcap_id);

    PGresult *messages = select(query_messages);
    int msg_num = PQntuples(messages);
    int fn_req;

    if (msg_num == 0) {
        printf("Pcap done.\n");
        continue;
    }

    char query_values[40];
    sprintf(query_values, "(%%d, %%d),\n");
    // sprintf(update_query, "UPDATE MESSAGES_%d AS M SET FN_REQ=E.FN_REQ FROM (VALUES ")
    int UPDT_LEN = msg_num * 40 + 100;
    printf("%d UPDATES FOR PCAP_%d\n", msg_num, pcap_id);
    char *updates = calloc(UPDT_LEN, 1);
    
    {
      int last_req = -1;
      int actual_req = 0;
      int cursor = 0;
      cursor += snprintf(updates, UPDT_LEN - cursor, "UPDATE MESSAGES_%d AS M SET FN_REQ=E.FN_REQ FROM (VALUES ", pcap_id);
    
      // printf("generating query...\n");
      for (int j = 0; j < msg_num; ++j) {
        int id = atoi(PQgetvalue(messages, j, 0));
        int isr = atoi(PQgetvalue(messages, j, 1));

        if (!isr) {
          ++last_req;
          fn_req = last_req;
          actual_req = last_req;
        } else {
          fn_req = actual_req;
        }

        cursor += snprintf(updates + cursor, UPDT_LEN - cursor, query_values,
                           fn_req, id);
      }
      cursor -= 2;

      // printf("\n--%d > %d\n", cursor, UPDT_LEN);
      // printf("updating...\n");

      cursor += snprintf(updates + cursor, UPDT_LEN - cursor, ") AS E(FN_REQ, ID)  WHERE M.ID=E.ID");
      // printf("\n--%d > %d\n", cursor, UPDT_LEN);

      update(updates);

      printf("updated.\n");
    }

    PQclear(messages);
  }

  PQclear(pcaps);
  PQfinish(conn);

  return 0;
}