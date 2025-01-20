import ee

def sort_by_date(image_list):
    """
    Sort the list of imagery from oldest to newest based on the date metadata.
    Args:
        image_list (list): List of image metadata dictionaries with a 'date' key.
    Returns:
        list: Sorted list of imagery.
    """
    return sorted(
        image_list,
        key=lambda img: img["date"]  # Use the 'date' key directly
    )

def calculate_aoi_coverage(image, aoi_geom):
    """
    Calculate the percentage of the AOI covered by the imagery.
    Args:
        image (ee.Image): Earth Engine Image object.
        aoi_geom (ee.Geometry): Area of Interest as an Earth Engine Geometry.
    Returns:
        float: Percentage of AOI covered by the image.
    """
    # Calculate the intersection of the image footprint with the AOI
    image_footprint = image.geometry()
    intersection = image_footprint.intersection(aoi_geom, ee.ErrorMargin(1))
    intersection_area = intersection.area().getInfo()
    aoi_area = aoi_geom.area().getInfo()

    return (intersection_area / aoi_area) * 100

def sort_by_coverage(image_list, aoi_geom):
    """
    Sort the list of imagery by percentage of AOI covered.
    Args:
        image_list (list): List of Earth Engine image metadata dictionaries.
        aoi_geom (ee.Geometry): Area of Interest as an Earth Engine Geometry.
    Returns:
        list: Sorted list of imagery.
    """
    image_list_with_coverage = [
        {
            **img,
            "coverage": calculate_aoi_coverage(ee.Image(img["id"]), aoi_geom)
        }
        for img in image_list
    ]

    return sorted(image_list_with_coverage, key=lambda img: img["coverage"], reverse=True)
