create table public.users
(
    telegram_id integer not null
        constraint users_pk
            primary key,
    first_name  text    not null,
    last_name   text    not null,
    username    text    not null,
    timezone    text
);

alter table public.users
    owner to postgres;

create table public.categories
(
    id   integer generated always as identity
        constraint categories_pk
            primary key,
    name text not null
);

alter table public.categories
    owner to postgres;

create table public.users_categories
(
    id          integer generated always as identity
        constraint users_categories_pk
            primary key,
    user_id     integer not null
        constraint users_categories_users_telegram_id_fk
            references public.users,
    category_id integer not null
        constraint users_categories_categories_id_fk
            references public.categories
);

alter table public.users_categories
    owner to postgres;

create table public.users_expenses
(
    id               integer generated always as identity
        constraint users_expenses_pk
            primary key,
    name             text,
    amount           double precision not null,
    user_category_id integer          not null
        constraint users_expenses_users_categories_id_fk
            references public.users_categories
            on delete cascade,
    date             date             not null
);

alter table public.users_expenses
    owner to postgres;


