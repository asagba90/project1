create table books (
    id SERIAL PRIMARY KEY,
    isbn VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    author VARCHAR NOT NULL,
    year INTEGER NOT NULL
);

create table reviews (
    id SERIAL PRIMARY KEY,
    isbn VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    author VARCHAR NOT NULL,
    year INTEGER NOT NULL
);

create table accounts (
	id SERIAL PRIMARY KEY,
	usersname VARCHAR NOT NULL,
	password VARCHAR NOT NULL,
	email VARCHAR NOT NULL
);

insert into accounts (usersname, password, email) values ('test', 'test', 'test@email.com');