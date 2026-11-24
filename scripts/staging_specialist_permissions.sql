-- Apply only to the owner-approved, disposable valhalla_staging database.
-- Run as its migration operator after creating the two dedicated LOGIN roles.
-- Supply odin_assignment and njord_assignment as psql variables containing approved UUIDs.
\set ON_ERROR_STOP on
BEGIN;
SELECT current_database() = 'valhalla_staging' AS staging_target \gset
\if :staging_target
\else
DO $$ BEGIN RAISE EXCEPTION 'Expected the isolated valhalla_staging database'; END $$;
\endif

-- Fail unless the two assignments exist, differ, and match their respective role.
SELECT (SELECT count(*) FROM prime_specialist_assignments
        WHERE (id = :'odin_assignment'::uuid AND role = 'ODIN')
           OR (id = :'njord_assignment'::uuid AND role = 'NJORD')) = 2 AS assignments_ready \gset
\if :assignments_ready
\else
DO $$ BEGIN RAISE EXCEPTION 'Missing exact ODIN and NJORD assignments'; END $$;
\endif

ALTER TABLE legacy_orchestration_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE prime_specialist_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE prime_specialist_triggers ENABLE ROW LEVEL SECURITY;

-- These permissive policies preserve ordinary table ACLs. Restrictive specialist policies below
-- limit even an inherited permissive policy. The runtime rejects specialist role membership.
CREATE POLICY pantheon_stage_existing_event_acl ON legacy_orchestration_events USING (true);
CREATE POLICY pantheon_stage_existing_assignment_acl ON prime_specialist_assignments USING (true);
CREATE POLICY pantheon_stage_existing_trigger_acl ON prime_specialist_triggers USING (true);

-- Quote values with format(%L); only fixed local role names are used as identifiers.
SELECT format($policy$
CREATE POLICY pantheon_stage_assignments_exact ON prime_specialist_assignments AS RESTRICTIVE
TO valhalla_stage_odin, valhalla_stage_njord
USING ((current_user = 'valhalla_stage_odin' AND id = %L::uuid)
    OR (current_user = 'valhalla_stage_njord' AND id = %L::uuid));
CREATE POLICY pantheon_stage_triggers_exact ON prime_specialist_triggers AS RESTRICTIVE
TO valhalla_stage_odin, valhalla_stage_njord
USING ((current_user = 'valhalla_stage_odin' AND assignment_id = %L::uuid)
    OR (current_user = 'valhalla_stage_njord' AND assignment_id = %L::uuid));
$policy$, :'odin_assignment', :'njord_assignment', :'odin_assignment', :'njord_assignment') \gexec

CREATE POLICY pantheon_stage_report_insert_only ON legacy_orchestration_events AS RESTRICTIVE
FOR INSERT TO valhalla_stage_odin, valhalla_stage_njord WITH CHECK (
    event_type = 'PANTHEON_ASSIGNMENT_REPORT' AND event_id ~ '^GOD-[0-9a-f]{64}$'
    AND EXISTS (SELECT 1 FROM prime_specialist_assignments a
        WHERE a.id::text = (payload_json::jsonb ->> 'assignment_id')
          AND a.role = (payload_json::jsonb ->> 'role')
          AND a.scope::jsonb = (payload_json::jsonb -> 'scope')
          AND a.scope ->> 'legacy_instance_id' = legacy_orchestration_events.legacy_instance_id)
);

-- Permit only the journal reads needed for source and outcome verification in the one pilot Legacy.
CREATE POLICY pantheon_stage_event_read_exact ON legacy_orchestration_events AS RESTRICTIVE
FOR SELECT TO valhalla_stage_odin, valhalla_stage_njord USING (
    EXISTS (SELECT 1 FROM prime_specialist_assignments a
        WHERE a.scope ->> 'legacy_instance_id' = legacy_orchestration_events.legacy_instance_id)
);

REVOKE ALL ON legacy_orchestration_events, prime_specialist_assignments, prime_specialist_triggers
FROM valhalla_stage_odin, valhalla_stage_njord;
GRANT SELECT, INSERT ON legacy_orchestration_events TO valhalla_stage_odin, valhalla_stage_njord;
GRANT SELECT, UPDATE (next_due_at, pending_event_id, last_report_event_id)
ON prime_specialist_assignments TO valhalla_stage_odin, valhalla_stage_njord;
GRANT SELECT, DELETE, UPDATE (failure_code) ON prime_specialist_triggers
TO valhalla_stage_odin, valhalla_stage_njord;
GRANT USAGE ON SEQUENCE legacy_orchestration_events_id_seq TO valhalla_stage_odin, valhalla_stage_njord;
COMMIT;
