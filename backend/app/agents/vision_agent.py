"""
Module 5.1/5.2 - Vision Agent: Redness-Index Inflammation Scoring

Implements the exact formula specified in the proposal (Chapter 4.5):
"The index is calculated as twice the red channel value minus the green
and blue channels, which is then used to count significant red pixels
over the total pixels in the image."

  redness_index(pixel) = 2*R - G - B

A pixel is counted as "significantly red" if this index exceeds a
threshold. The inflammation score is the fraction of significantly red
pixels over the total pixel count.

HONEST LIMITATIONS (state these in the report):
  - This is a simple, interpretable heuristic, not a trained model. It
    will flag any predominantly red/pink region -- it cannot distinguish
    cellulitis from a sunburn, a rash, or even red clothing in frame. A
    real clinical deployment would need a proper trained classifier and
    a controlled photo capture protocol (consistent lighting/distance).
  - No real dermatological image dataset was available to validate
    against (our vignette dataset has no images) -- this is tested only
    on synthetic test images we generate ourselves below, which proves
    the MATH is implemented correctly, not that it's clinically accurate
    on real skin photos.
"""
import numpy as np
from PIL import Image


REDNESS_THRESHOLD = 60  # UNCALIBRATED -- see module docstring limitation below.
# This value is a placeholder, not derived from real clinical images. Testing
# revealed it's sensitive to overall pixel brightness, not just "how red
# something looks" -- e.g. a pale pink (255,220,220) scores 70 (2*255-220-220),
# which exceeds this threshold despite being a mild tint, not a strong red.
# This is a genuine limitation of the 2R-G-B formula as specified in the
# proposal: because R is doubled, a bright/light pixel with even a small
# R-vs-G/B gap can score as "significantly red." A real deployment needs
# this threshold calibrated against actual dermatological photos (which we
# don't have access to) -- state this explicitly as required future work,
# not a solved problem.


def compute_redness_index(image: Image.Image) -> np.ndarray:
    """Returns a 2D array of the redness index for every pixel."""
    arr = np.asarray(image.convert("RGB"), dtype=np.int16)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    return 2 * r - g - b


def inflammation_score(image: Image.Image, threshold: int = REDNESS_THRESHOLD) -> dict:
    """
    Returns the inflammation score (fraction of significantly red pixels)
    plus supporting detail for the auditable decision trail.
    """
    redness = compute_redness_index(image)
    total_pixels = redness.size
    red_pixel_count = int(np.sum(redness > threshold))
    score = red_pixel_count / total_pixels

    return {
        "inflammation_score": round(score, 4),
        "significant_red_pixels": red_pixel_count,
        "total_pixels": total_pixels,
        "threshold_used": threshold,
        "interpretation": _interpret(score),
    }


def _interpret(score: float) -> str:
    if score >= 0.5:
        return "High redness coverage -- possible significant inflammation/cellulitis, correlate with clinical exam"
    elif score >= 0.2:
        return "Moderate redness coverage -- possible localized inflammation"
    elif score >= 0.05:
        return "Mild/minor redness detected"
    else:
        return "No significant redness detected"


def vision_agent(image_path: str) -> dict:
    """Main entry point -- loads an image file and returns the analysis."""
    image = Image.open(image_path)
    return inflammation_score(image)


def vision_flag_for_triage(vision_result: dict) -> bool:
    """
    Module 5.3 - Wires Vision Agent output into the diagnosis/triage
    reasoning. Returns True if the image evidence alone warrants treating
    this as a possible-cellulitis red flag (feeds into the rule engine
    as an additional signal, alongside vitals and reported symptoms).
    High threshold (0.5) deliberately chosen given the known threshold
    calibration limitation above -- we'd rather under-flag on ambiguous
    images than let an uncalibrated heuristic drive urgent escalations
    on its own.
    """
    return vision_result["inflammation_score"] >= 0.5


if __name__ == "__main__":
    # Build synthetic test images (no real dermatological dataset available
    # -- see module docstring). These prove the MATH is correct, not
    # clinical accuracy on real photos.
    import os
    os.makedirs("test_images", exist_ok=True)

    # Test 1: solid red square on white background (50% of image is "red")
    img1 = Image.new("RGB", (100, 100), (255, 255, 255))
    red_half = np.array(img1)
    red_half[:, :50] = [220, 60, 60]  # left half strongly red
    Image.fromarray(red_half).save("test_images/half_red.png")

    # Test 2: entirely white (no redness at all)
    Image.new("RGB", (100, 100), (255, 255, 255)).save("test_images/all_white.png")

    # Test 3: entirely red (maximum redness)
    Image.new("RGB", (100, 100), (255, 0, 0)).save("test_images/all_red.png")

    # Test 4: pale pink tint -- demonstrates the KNOWN LIMITATION above.
    # A human would call this "barely pink," but 2R-G-B still exceeds our
    # uncalibrated threshold. Included deliberately, not to hide it.
    Image.new("RGB", (100, 100), (255, 220, 220)).save("test_images/pale_pink_known_limitation.png")

    # Test 5: very subtle off-white tint, should genuinely score near zero
    Image.new("RGB", (100, 100), (255, 250, 248)).save("test_images/near_white.png")

    for name in ["half_red", "all_white", "all_red", "pale_pink_known_limitation", "near_white"]:
        result = vision_agent(f"test_images/{name}.png")
        print(f"\n--- {name} ---")
        print(f"Score: {result['inflammation_score']} ({result['significant_red_pixels']}/{result['total_pixels']} pixels)")
        print(f"Interpretation: {result['interpretation']}")
