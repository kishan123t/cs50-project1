import os, csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# the engine object from sqlalchemy that  manage connections to the database
URL=""
engine = create_engine('postgres://ioazouxpumlxzt:99d9184dab9030545216426d35f3f174ec2cb81ce1a665eb8cc2d23a371553bc@ec2-34-200-72-77.compute-1.amazonaws.com:5432/db64210elk5kma')


#create a scop of session that ensure diffrent user intraction
db=scoped_session(sessionmaker(bind=engine))

#open a csv file to import in DATABASE_URL
file=open("books.csv")

reader=csv.reader(file)

#loop for insert data into database
for isbn,title,author,year in reader:
    db.execute("INSERT INTO books (isbn,title,author,year) VALUES (:isbn,:title,:author,:year)",
    {
    "isbn":isbn,
    "title":title,
    "author":author,
    "year":year
    })
    print('Added Book :',title)
print("all books Added")

db.commit()
