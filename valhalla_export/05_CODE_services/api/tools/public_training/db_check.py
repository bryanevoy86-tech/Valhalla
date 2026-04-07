import os
from sqlalchemy import create_engine, text

engine = create_engine(os.environ["DATABASE_URL"], future=True)
with engine.begin() as conn:
    a = conn.execute(text("SELECT COUNT(*) FROM public_training_properties")).scalar()
    b = conn.execute(text("SELECT COUNT(*) FROM public_training_labels")).scalar()

print("public_training_properties:", a)
print("public_training_labels:", b)
