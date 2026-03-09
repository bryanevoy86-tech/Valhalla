"""Lightweight ID generator utility for appointments and entities."""
import uuid
import time
from datetime import datetime


def generate_uuid() -> str:
    """Generate a UUID4 string."""
    return str(uuid.uuid4())


def generate_id() -> str:
    """
    Generate a universal ID for any entity.
    Uses Snowflake-like approach with timestamp + random suffix.
    """
    timestamp = int(time.time() * 1000)
    random_suffix = uuid.uuid4().hex[:12]
    return f"{timestamp}{random_suffix}"

    """
    Generate a Snowflake-like distributed ID.
    
    Uses timestamp, worker_id, and random bits to create a unique ID.
    Compatible with existing pack modules.
    """
    # Timestamp: milliseconds since epoch (41 bits)
    timestamp = int(time.time() * 1000)
    
    # Worker ID (5 bits) + Datacenter ID (5 bits) = 10 bits
    worker_bits = (worker_id & 0x1f) << 5
    datacenter_bits = datacenter_id & 0x1f
    
    # Sequence number (12 bits) - using part of microsecond as sequence
    sequence = int(time.time() * 1000000) % 0xfff
    
    # Combine: timestamp(41) | worker(5) | datacenter(5) | sequence(12) = 63 bits
    snowflake_id = (timestamp << 22) | (worker_bits << 17) | (datacenter_bits << 12) | sequence
    
    return snowflake_id


def generate_slug(prefix: str = "", entity_type: str = "") -> str:
    """
    Generate a human-readable slug with optional prefix.
    
    Format: prefix_entitytype_timestamp_random
    """
    timestamp = int(time.time() * 1000)
    random_suffix = uuid.uuid4().hex[:8]
    
    parts = [prefix, entity_type, str(timestamp), random_suffix]
    slug = "_".join([p for p in parts if p])
    return slug


def generate_appointment_id(appointment_type: str = "") -> str:
    """
    Generate a unique appointment ID.
    
    Format: APT_<type>_<timestamp>_<random>
    """
    return generate_slug(prefix="APT", entity_type=appointment_type)


def generate_entity_id(entity_type: str) -> str:
    """
    Generate a unique entity ID for any resource.
    
    Format: <type>_<timestamp>_<random>
    """
    return generate_slug(entity_type=entity_type)
