"""
GPU detection and configuration utility.

This module helps detect and configure GPU settings for the embedding service.
"""

import logging
import os
from typing import Optional

try:
    import torch
except ImportError:
    torch = None

logger = logging.getLogger(__name__)

# Cache device detection to avoid repeated slow CUDA calls
_device_info_cache: Optional[dict] = None

def detect_device() -> str:
    """
    Detect the best available device for embeddings.
    Uses cached result if available.

    Returns:
        Device string: 'cuda', 'cpu', or 'mps' (Apple Silicon)
    """
    global _device_info_cache
    
    if torch is None:
        return "cpu"
    
    # Quick check first (fast)
    if not torch.cuda.is_available():
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
        return "cpu"
    
    # CUDA is available - this is the slow part, but only happens once
    return "cuda"


def get_device_info() -> dict:
    """
    Get detailed information about available devices.
    Uses cached result to avoid repeated slow CUDA calls.

    Returns:
        Dictionary with device information
    """
    global _device_info_cache
    
    # Return cached result if available
    if _device_info_cache is not None:
        return _device_info_cache
    
    info = {
        "device": detect_device(),
        "torch_available": torch is not None,
        "cuda_available": False,
        "cuda_device_count": 0,
        "cuda_device_name": None,
        "mps_available": False,
    }

    if torch is not None:
        info["cuda_available"] = torch.cuda.is_available()
        # Only get detailed CUDA info if CUDA is available (avoid slow calls)
        if info["cuda_available"]:
            try:
                info["cuda_device_count"] = torch.cuda.device_count()
                info["cuda_device_name"] = torch.cuda.get_device_name(0)
            except Exception:
                # CUDA might be available but not fully initialized
                pass

        if hasattr(torch.backends, "mps"):
            info["mps_available"] = torch.backends.mps.is_available()
    
    # Cache the result
    _device_info_cache = info
    return info


def print_device_info():
    """Print device information to console."""
    info = get_device_info()
    print("\n" + "=" * 60)
    print("Device Information")
    print("=" * 60)
    print(f"PyTorch available: {info['torch_available']}")
    print(f"Current device: {info['device']}")
    print(f"CUDA available: {info['cuda_available']}")
    if info["cuda_available"]:
        print(f"  GPU count: {info['cuda_device_count']}")
        print(f"  GPU name: {info['cuda_device_name']}")
    print(f"MPS available (Apple Silicon): {info['mps_available']}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    print_device_info()

