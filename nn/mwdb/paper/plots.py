from re import DEBUG
import psycopg2
import pandas as pd
import utils
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
import os

eng = create_engine("postgresql://postgres:postgres@localhost/dns",)
db = psycopg2.connect("host=localhost dbname=dns user=postgres password=postgres")


messages = pd.read_sql("SELECT * FROM public.DN_GROUPED", eng)

messages['labels'] = messages.dn.apply(lambda dn: 1 + dn.count("."))

mg = messages.groupby("labels").aggregate({ "COUNT": "sum" })
mg = mg.rename(columns={ 'COUNT': 'count' })
mg['%'] = ((mg['count'] / mg['count'].sum()) * 100)
mg['%'] = mg['%'].round(2)

print(mg)


mg = messages.groupby("labels").aggregate({ "dn": "count" })
mg['%'] = ((mg['dn'] / mg['dn'].sum()) * 100)
mg['%'] = mg['%'].round(2)
print(mg)


training = pd.read_csv('/home/princio/Desktop/malware_detection/training/dataset_training.csv')

training['labels'] = training.dn.apply(lambda dn: 1 + dn.count("."))

training['c'] = 1

tg = training[['legit', 'labels', 'dn']].groupby(['legit', 'labels']).aggregate({
    'dn': 'count'
})

print(tg.unstack().transpose().fillna(0).astype(int))


# pcap = pd.read_sql("SELECT * FROM pcap", db)

# print(pcap.malware_id.value_counts())

# pcap["infected"] = pcap.malware_id.apply(lambda mwid: "healthy" if mwid == 28 else "infected")

# pcapg = pcap.groupby("infected").aggregate({
#     "qr": ["std", "mean"],
#     "days": ["std", "mean"]
# })


# fig, axs = plt.subplots(4, sharex=True)
# idx = pd.IndexSlice

# p1 = pcapg.loc[:, idx["qr", :]].plot.bar(ax=axs[0])
# pcapg.loc[:, idx["days", :]].plot.bar(ax=axs[1])


# for bar in p1.patches:
   
#   # Using Matplotlib's annotate function and
#   # passing the coordinates where the annotation shall be done
#   # x-coordinate: bar.get_x() + bar.get_width() / 2
#   # y-coordinate: bar.get_height()
#   # free space to be left to make graph pleasing: (0, 8)
#   # ha and va stand for the horizontal and vertical alignment
#     p1.annotate(format(bar.get_height(), '.0f'),
#                    (bar.get_x() + bar.get_width() / 2,
#                     bar.get_height()), ha='center', va='center',
#                    size=12, xytext=(0, 8),
#                    textcoords='offset points')


# print(pcapg.loc[:, idx["qr", :]])

# plt.show()