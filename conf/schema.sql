-- drop database if exists Kaguyahime;

create database IF NOT EXISTS Kaguyahime;

use Kaguyahime;

grant select, insert, update, delete on Kaguyahime.* to 'www-data'@'localhost';

create table IF NOT EXISTS users (
    `id` varchar(50) not null,
    `email` varchar(50) not null,
    `passwd` varchar(50) not null,
    `admin` bool not null,
    `name` varchar(50) not null,
    `image` varchar(500) not null,
    `created_at` real not null,
    unique key `idx_email` (`email`),
    key `idx_created_at` (`created_at`),
    primary key (`id`)
) engine=innodb default charset=utf8;

create table IF NOT EXISTS blogs (
    `id` varchar(50) not null,
    `user_id` varchar(50) not null,
    `user_name` varchar(50) not null,
    `user_image` varchar(500) not null,
    `name` varchar(50) not null,
    `summary` varchar(200) not null,
    `content` mediumtext not null,
    `created_at` real not null,
    key `idx_created_at` (`created_at`),
    primary key (`id`)
) engine=innodb default charset=utf8;

create table IF NOT EXISTS comments (
    `id` varchar(50) not null,
    `blog_id` varchar(50) not null,
    `user_id` varchar(50) not null,
    `user_name` varchar(50) not null,
    `user_image` varchar(500) not null,
    `content` mediumtext not null,
    `created_at` real not null,
    key `idx_created_at` (`created_at`),
    primary key (`id`)
) engine=innodb default charset=utf8;

create table IF NOT EXISTS tags (
    `id` varchar(50) not null,
    `name` varchar(50) not null,
    key `idx_name` (`name`),
    primary key (`id`)
) engine=innodb default charset=utf8;

create table IF NOT EXISTS blog_tag (
    `id` varchar(50) not null,
    `blog_id` varchar(50) not null,
    `tag_id` varchar(50) not null,
    key `idx_blog_id` (`blog_id`),
    key `idx_tag_id` (`tag_id`),
    primary key (`id`)
) engine=innodb default charset=utf8;
