alter table records add column metadata TEXT;
alter table records add column metadata_type TEXT default 'application/xml';
alter table records add column edition TEXT;
alter table records add column contacts TEXT;
alter table records add column themes TEXT;
vacuum;
