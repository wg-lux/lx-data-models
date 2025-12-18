from lx_dtypes.models.base_models.base_model import AppBaseModel

POLYP_DF_COLUMNS = [
    "record_id",
    "ai",  # 1 / 0
    "location_segment",  # ascendens,cecum,descendens,left_flexure,rectum,right_flexure,sigma,transversum
    "location_cm",  # int, -1 if missing
    "size_category",  # str, "<6", "6-9", "10-20", ">20"
    "size_mm",  # int or None / np.nan if missing
    "rating",  # empty, hyperplastic,inflammatory,malign,ssl,tubular_adenoma,tubulorvillous_adenoma
    "paris",  # set string like: "{Is,IIa}", remove quotes and braces, then split by comma, then map
    "dysplasia",  # True / False / low / high / none
    "histo",  # ssl / adenoma
    "resection_technique",  # biopsy / enbloc / piecemeal / None
    "resection_status_microscopic",  # R0, R1, None
    "resection",  # True / False / 1.0
    "salvage",  # "complete", "none" (literal string), partial
    "shape",  # unknown / pedunculated / sessile / flat / "flat + sessile"
    "location_coarse",  # right_hemicolon, left_hemicolon, rectum, cecum
    "non_lifting_sign",  # None / True / False
    "tool",  # "snare", "snare_cold", "snare_hot", "biopsy_forceps"
]

DROP_COLUMNS_POLYP_DF = [
    "number_clips",
    "no_resection_reason",
    "injection",
    "apc_watts",
    "salvage_old",
    "resection_old",
    "surface_intact",
    "morphology",
    "sedation",
    "Unnamed: 0",
    "ectomy_wound_care_old",
    "ectomy_wound_care_technique",
    "ectomy_wound_care_success",
    "nice",
    "lst",
    "ectomy_wound_care",
    "jar_id",
]

# Unnamed: 0","record_id","ai","sedation","location_segment","location_cm","size_category","size_mm","surface_intact","rating","paris","dysplasia","histo","morphology","nice","lst","non_lifting_sign","injection","resection_old","tool","resection_technique","resection_status_microscopic","salvage_old","apc_watts","number_clips","ectomy_wound_care_old","ectomy_wound_care_technique","ectomy_wound_care_success","no_resection_reason","resection","salvage","ectomy_wound_care","jar_id","shape","location_coarse


class SmartiePolypSchema(AppBaseModel):
    pass


class SmartiePolyps(AppBaseModel):
    pass
