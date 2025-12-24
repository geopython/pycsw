alter table records add column metadata TEXT;
alter table records add column metadata_type TEXT default 'application/xml';
alter table records add column edition TEXT;
alter table records add column contacts TEXT;
alter table records add column themes TEXT;
alter table records add column illuminationelevationangle TEXT;
alter table records alter column cloudcover type real using cast(cloudcover as float);
alter table records alter column distancevalue type real using cast(distancevalue as float);
vacuum;
