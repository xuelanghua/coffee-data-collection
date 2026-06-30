from datetime import date

from apps.coffee.models import CollectionEvent, PhotoAsset, Plot, Point


PREFIX_TO_MODEL_FIELD = {
    "PL": (Plot, "plot_id"),
    "PT": (Point, "point_id"),
    "EV": (CollectionEvent, "event_id"),
    "PH": (PhotoAsset, "photo_id"),
}


def next_business_id(prefix, today=None):
    if prefix not in PREFIX_TO_MODEL_FIELD:
        raise ValueError(f"Unsupported business id prefix: {prefix}")
    day = (today or date.today()).strftime("%Y%m%d")
    stem = f"{prefix}{day}"
    model, field_name = PREFIX_TO_MODEL_FIELD[prefix]
    latest = (
        model.objects.filter(**{f"{field_name}__startswith": stem})
        .order_by(f"-{field_name}")
        .values_list(field_name, flat=True)
        .first()
    )
    next_sequence = 1
    if latest:
        try:
            next_sequence = int(str(latest)[len(stem):]) + 1
        except ValueError:
            next_sequence = 1
    return f"{stem}{next_sequence:04d}"
