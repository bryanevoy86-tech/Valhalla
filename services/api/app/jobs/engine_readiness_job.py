"""
Engine readiness evaluator - daily job to promote engines when metrics qualify.
"""

from datetime import datetime
from sqlalchemy.orm import Session

from app.models.engine_readiness import EngineReadiness
from app.governance.engine_rules import ENGINE_RULES


def evaluate_engine_readiness(db: Session, engine_name: str = None) -> dict:
    """
    Evaluate engine(s) for promotion.
    
    If engine_name is provided, evaluate that one.
    Otherwise, evaluate all SANDBOX engines.
    
    Returns dict with evaluation results.
    """
    results = {}
    now = datetime.utcnow()
    
    # Determine which engines to evaluate
    engines_to_check = [engine_name] if engine_name else list(ENGINE_RULES.keys())
    
    for eng_name in engines_to_check:
        row = db.query(EngineReadiness).filter_by(engine_name=eng_name).first()
        
        if not row:
            results[eng_name] = {"status": "not_found"}
            continue
        
        # Only evaluate SANDBOX engines
        if row.state != "SANDBOX":
            results[eng_name] = {"status": "not_sandbox", "current_state": row.state}
            continue
        
        rules = ENGINE_RULES.get(eng_name)
        if not rules:
            results[eng_name] = {"status": "no_rules_defined"}
            continue
        
        # Wholesaling: check approval rate and false positive rate
        if eng_name == "wholesaling":
            passes_samples = row.sample_size and row.sample_size >= rules["min_samples"]
            passes_approval = row.approval_rate and row.approval_rate >= rules["min_approval_rate"]
            passes_fp_rate = row.false_positive_rate and row.false_positive_rate <= rules["max_fp_rate"]
            
            if passes_samples and passes_approval and passes_fp_rate:
                row.state = "READY"
                row.evaluated_at = now
                db.add(row)
                results[eng_name] = {
                    "status": "promoted_to_ready",
                    "samples": row.sample_size,
                    "approval_rate": row.approval_rate,
                    "fp_rate": row.false_positive_rate,
                }
            else:
                results[eng_name] = {
                    "status": "not_ready",
                    "passes_samples": passes_samples,
                    "passes_approval": passes_approval,
                    "passes_fp_rate": passes_fp_rate,
                    "current_metrics": {
                        "samples": row.sample_size,
                        "approval_rate": row.approval_rate,
                        "fp_rate": row.false_positive_rate,
                    },
                    "required": {
                        "min_samples": rules["min_samples"],
                        "min_approval_rate": rules["min_approval_rate"],
                        "max_fp_rate": rules["max_fp_rate"],
                    },
                }
        
        # Arbitrage: simpler rules (just sample size + ROI)
        elif eng_name == "arbitrage":
            passes_samples = row.sample_size and row.sample_size >= rules["min_samples"]
            
            if passes_samples:
                row.state = "READY"
                row.evaluated_at = now
                db.add(row)
                results[eng_name] = {
                    "status": "promoted_to_ready",
                    "samples": row.sample_size,
                }
            else:
                results[eng_name] = {
                    "status": "not_ready",
                    "samples": row.sample_size,
                    "min_samples": rules["min_samples"],
                }
        
        # Trading advisory: placeholder
        elif eng_name == "trading_advisory":
            results[eng_name] = {
                "status": "not_yet_evaluated",
                "reason": "trading_advisory evaluation not yet implemented",
            }
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        results["error"] = str(e)
    
    return results
