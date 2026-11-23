create extension if not exists vector;
create extension if not exists pg_trgm;

create table data_release (
    id serial primary key,
    created_at timestamptz not null default now(),
    notes text not null default ''
);

create table kbli (
    code text not null,
    data_release_id integer not null references data_release (id),
    version text not null default '2025',
    title text not null,
    definition text not null,
    in_scope boolean not null,
    embedding vector(1024),
    search_tsv tsvector generated always as
        (to_tsvector('simple', title || ' ' || definition)) stored,
    primary key (code, data_release_id)
);
create index kbli_search_tsv_idx on kbli using gin (search_tsv);
create index kbli_title_trgm_idx on kbli using gin (title gin_trgm_ops);

create table kbli_2020_map (
    data_release_id integer not null references data_release (id),
    code_2020 text not null,
    code_2025 text not null,
    primary key (data_release_id, code_2020, code_2025)
);

create table permit (
    id text not null,
    data_release_id integer not null references data_release (id),
    name text not null,
    issuer text not null,
    description text not null,
    how_to text not null,
    source_regulation text not null,
    source_article text,
    source_url text not null,
    valid_from date not null,
    valid_to date,
    last_verified date not null,
    regional_note text,
    primary key (id, data_release_id)
);

create table permit_rule (
    id serial primary key,
    data_release_id integer not null references data_release (id),
    kbli_code text not null,
    conditions jsonb not null default '{}',
    risk_level text not null
        check (risk_level in ('rendah', 'menengah_rendah', 'menengah_tinggi', 'tinggi')),
    permit_id text not null,
    step_order integer not null,
    source_regulation text not null,
    source_url text not null,
    valid_from date not null,
    valid_to date,
    last_verified date not null,
    foreign key (permit_id, data_release_id) references permit (id, data_release_id)
);
create index permit_rule_kbli_idx on permit_rule (data_release_id, kbli_code);

create table query_log (
    id serial primary key,
    created_at timestamptz not null default now(),
    input text not null,
    attributes jsonb,
    clarifications jsonb,
    output jsonb,
    data_release_id integer references data_release (id),
    model text,
    tokens_in integer,
    tokens_out integer,
    cost_usd numeric(10, 6),
    latency_ms integer,
    helpful boolean,
    comment text
);
