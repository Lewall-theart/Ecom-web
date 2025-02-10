create database ecomdb;
use ecomdb;

create table Users (
    id int auto_increment not null,
    name varchar(100) not null,
    email varchar(100) unique not null,
    password varchar(255) not null,
    role varchar(10) not null,
    primary key (id)
);

create table Products (
    id int auto_increment not null,
    name varchar(100) not null,
    price float not null,
    amount int not null,
    description varchar(300) not null,
    primary key (id)
);

create table Cart (
    id int auto_increment not null,
    user_id int not null,
    product_id int not null,
    amount int not null,
    primary key (id),
    foreign key (user_id) references Users(id) on delete cascade,
    foreign key (product_id) references Products(id) on delete cascade
);
