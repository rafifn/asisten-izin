-- Opaque public id for a logged request (the serial id is never exposed by the API).
alter table query_log add column request_uuid uuid not null default gen_random_uuid();
create unique index query_log_request_uuid_idx on query_log (request_uuid);
