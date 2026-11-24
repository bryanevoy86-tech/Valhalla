"""Verify effective specialist staging credentials before polling work."""
from fastapi import HTTPException
from sqlalchemy import text


def require_restricted_session(db, expected_role):
    if db.get_bind().dialect.name != "postgresql":
        raise HTTPException(503, "Specialist staging requires PostgreSQL")
    readiness = db.execute(text("""
        SELECT current_database() = 'valhalla_staging'
            AND current_user = :expected_role AND session_user = current_user
            AND NOT (r.rolsuper OR r.rolbypassrls OR r.rolcreaterole OR r.rolcreatedb OR r.rolreplication)
            AND NOT EXISTS (SELECT FROM pg_auth_members m WHERE m.member = r.oid)
            AND NOT has_schema_privilege(current_user, current_schema(), 'CREATE')
            AND has_table_privilege(current_user, 'legacy_orchestration_events', 'INSERT')
            AND NOT has_any_column_privilege(current_user, 'legacy_orchestration_events', 'UPDATE')
            AND NOT has_table_privilege(current_user, 'legacy_orchestration_events', 'DELETE, TRUNCATE, TRIGGER')
            AND NOT has_any_column_privilege(current_user, 'prime_specialist_assignments', 'INSERT')
            AND NOT has_table_privilege(current_user, 'prime_specialist_assignments', 'DELETE, TRUNCATE, TRIGGER')
            AND NOT EXISTS (SELECT FROM unnest(ARRAY['id', 'role', 'scope', 'scope_key', 'state',
                                                      'cadence_seconds', 'expires_at']) AS column_name
                WHERE has_column_privilege(current_user, 'prime_specialist_assignments', column_name, 'UPDATE'))
            AND NOT has_any_column_privilege(current_user, 'prime_specialist_triggers', 'INSERT')
            AND NOT has_column_privilege(current_user, 'prime_specialist_triggers', 'assignment_id', 'UPDATE')
            AND NOT has_column_privilege(current_user, 'prime_specialist_triggers', 'event_id', 'UPDATE')
            AND NOT has_table_privilege(current_user, 'prime_specialist_triggers', 'TRUNCATE, TRIGGER')
            AND EXISTS (SELECT FROM pg_policies
                WHERE schemaname = current_schema() AND tablename = 'legacy_orchestration_events'
                  AND policyname = 'pantheon_stage_report_insert_only' AND permissive = 'RESTRICTIVE'
                  AND current_user = ANY(roles) AND cmd = 'INSERT')
            AND (SELECT count(*) = 3 FROM pg_policies
                WHERE schemaname = current_schema() AND permissive = 'RESTRICTIVE' AND current_user = ANY(roles)
                  AND (tablename, policyname) IN (
                      ('legacy_orchestration_events', 'pantheon_stage_event_read_exact'),
                      ('prime_specialist_assignments', 'pantheon_stage_assignments_exact'),
                      ('prime_specialist_triggers', 'pantheon_stage_triggers_exact')))
            AND row_security_active('legacy_orchestration_events')
            AND row_security_active('prime_specialist_assignments')
            AND row_security_active('prime_specialist_triggers')
        FROM pg_roles r WHERE r.rolname = current_user
    """), {"expected_role": expected_role}).scalar_one()
    if readiness is not True:
        raise HTTPException(503, "Specialist staging database privileges are not restricted")
