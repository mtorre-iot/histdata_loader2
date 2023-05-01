Script to set datasource back in time (thanks: Gerhard Powell)

[3:09 PM] Gerhard Powell


UPDATE augustinian_petroleum.hierarchy_data_sources
SET start_time=start_time - 3 * INTERVAL '3 year', end_time= end_time - 3 * INTERVAL '3 year', edited_by='gerhard.powell@sensiaglobal.com', edited_time=now()
WHERE hierarchy_id = '5a4111bf-87e5-49a5-997a-92df0828a656' and end_time is not null;

UPDATE augustinian_petroleum.hierarchy_data_sources
SET start_time='2010-01-01 22:30:34.096', edited_by='gerhard.powell@sensiaglobal.com', edited_time=now()
WHERE hierarchy_id = '5a4111bf-87e5-49a5-997a-92df0828a656' and end_time is null;



