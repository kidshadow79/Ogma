from .perception import get_visual_events_context
from .memory_utils import caviarder_phrases_magiques_introspection, trigger_indexing_fn
from .image_generation import (
    process_image_generation,
    process_img2img_generation,
    analyze_i2i_result,
    request_i2i_stop,
    reset_i2i_stop,
    is_i2i_stop_requested,
    _parse_i2i_analysis_json,
    _prepare_image_for_vision,
    refine_i2i_prompt,
    generate_img2img_with_correction,
)
from .i2i_lessons import get_lessons_manager, cleanup_lessons, I2ILessonsManager, restructure_i2i_guide
