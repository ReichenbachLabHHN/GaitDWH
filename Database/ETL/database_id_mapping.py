"""
This module contains functions to map several ids from the individual databases to our global id-system.
"""
## PERSON ID

def get_global_person_id_hugadb(local_id):
    """
    Returns the global person_ID for a provided local subject_ID of the HuGaDB.

    Args:
        local_id (int):
            Local subject_ID of the HuGaDB

    Returns:
        (int/string):
            Global person_ID. Returns "Invalid ID" string instead, if subject_ID is unknown.
    """
    mapping = {
        1: 1,
        2: 2,
        3: 3,
        4: 4,
        5: 5,
        6: 6,
        7: 7,
        8: 8,
        9: 9,
        10: 10,
        11: 11,
        12: 12,
        13: 13,
        14: 14,
        15: 15,
        16: 16,
        17: 17,
        18: 18
    }
    return mapping.get(local_id, "Invalid ID")





def get_global_person_id_mcgill(local_id):
    """
    Returns the global person_ID for a provided local subject_ID of the McGill University Gait Dataset.

    Args:
        local_id (int):
            Local subject_ID of the McGill University Gait Dataset

    Returns:
        (int/string):
            Global person_ID. Returns "Invalid ID" string instead, if subject_ID is unknown.
    """
    mapping = {
        1: 19,
        2: 20,
        3: 21,
        4: 22,
        5: 23,
        6: 24,
        7: 25,
        8: 26,
        9: 27,
        10: 28,
        11: 29,
        12: 30,
        13: 31,
        14: 32,
        15: 33,
        16: 34,
        17: 35,
        18: 36,
        19: 37,
        20: 38
    }
    return mapping.get(local_id, "Invalid ID")







def get_global_person_id_marea(local_id):
    """
    Returns the global person_ID for a provided local subject_ID of the MAREA Gait Database.

    Args:
        local_id (int):
            Local subject_ID of the MAREA Gait Database

    Returns:
        (int/string):
            Global person_ID. Returns "Invalid ID" string instead, if subject_ID is unknown.
    """
    mapping = {
        
        1: 925,
        2: 926,
        3: 927,
        4: 928,
        5: 929,
        6: 930,
        7: 931,
        8: 932,
        9: 933,
        10: 934,
        11: 935,
        12: 925,
        13: 926,
        14: 927,
        15: 928,
        16: 929,
        17: 930,
        18: 931,
        19: 932,
        20: 933
        
    }
    return mapping.get(local_id, "Invalid ID")






def get_global_person_id_vajdi(local_id):
    """
    Returns the global person_ID for a provided local subject_ID of the Vajdi et al 2020 Gait Database.

    Args:
        local_id (int):
            Local subject_ID of the Vajdi et al 2020 Gait Database

    Returns:
        (int/string):
            Global person_ID. Returns "Invalid ID" string instead, if subject_ID is unknown.
    """
    mapping = {
        
        1: 39,
        2: 40,
        3: 41,
        4: 42,
        5: 43,
        6: 44,
        7: 45,
        8: 46,
        9: 47,
        10: 48,
        11: 49,
        12: 50,
        13: 51,
        14: 52,
        15: 53,
        16: 54,
        17: 55,
        18: 56,
        19: 57,
        20: 58,
        21: 59,
        22: 60,
        23: 61,
        24: 62,
        25: 63,
        26: 64,
        27: 65,
        28: 66,
        29: 67,
        30: 68,
        31: 69,
        32: 70,
        33: 71,
        34: 72,
        35: 73,
        36: 74,
        37: 75,
        38: 76,
        39: 77,
        40: 78,
        41: 79,
        42: 80,
        43: 81,
        44: 82,
        45: 83,
        46: 84,
        47: 85,
        48: 86,
        49: 87,
        50: 88,
        51: 89,
        52: 90,
        53: 91,
        54: 92,
        55: 93,
        56: 94,
        57: 95,
        58: 96,
        59: 97,
        60: 98,
        61: 99,
        62: 100,
        63: 101,
        64: 102,
        65: 103,
        66: 104,
        67: 105,
        68: 106,
        69: 107,
        70: 108,
        71: 109,
        72: 110,
        73: 111,
        74: 112,
        75: 113,
        76: 114,
        77: 115,
        78: 116,
        79: 117,
        80: 118,
        81: 119,
        82: 120,
        83: 121,
        84: 122,
        85: 123,
        86: 124,
        87: 125,
        88: 126,
        89: 127,
        90: 128,
        91: 129,
        92: 130,
        93: 131
        
    }
    return mapping.get(local_id, "Invalid ID")





def get_global_person_id_ou_isir(local_id):
    """
    Returns the global person_ID for a provided local subject_ID of the OU-ISIR Gait Database.

    Args:
        local_id (int):
            Local subject_ID of the OU-ISIR Gait Database

    Returns:
        (int/string):
            Global person_ID. Returns "Invalid ID" string instead, if subject_ID is unknown.
    """
    mapping = {

        104: 132,
        2318: 133,
        2422: 134,
        2526: 135,
        2630: 136,
        2734: 137,
        2838: 138,
        2942: 139,
        4636: 140,
        4948: 141,
        5223: 142,
        5327: 143,
        5431: 144,
        5535: 145,
        5639: 146,
        7853: 147,
        8440: 148,
        9131: 149,
        9443: 150,
        9547: 151,
        9859: 152,
        9963: 153,
        10002: 154,
        13011: 155,
        13115: 156,
        13635: 157,
        13739: 158,
        13843: 159,
        14222: 160,
        14638: 161,
        14950: 162,
        15953: 163,
        16020: 164,
        16124: 165,
        16228: 166,
        17127: 167,
        17439: 168,
        18650: 169,
        18962: 170,
        19029: 171,
        19341: 172,
        19445: 173,
        20212: 174,
        20732: 175,
        21423: 176,
        21527: 177,
        21631: 178,
        21735: 179,
        21839: 180,
        21943: 181,
        22218: 182,
        22322: 183,
        22530: 184,
        22842: 185,
        24744: 186,
        51013: 187,
        51221: 188,
        51845: 189,
        53019: 190,
        53123: 191,
        53227: 192,
        53643: 193,
        53955: 194,
        54022: 195,
        54126: 196,
        54230: 197,
        54334: 198,
        54438: 199,
        57863: 200,
        57967: 201,
        58034: 202,
        58138: 203,
        58242: 204,
        58346: 205,
        58762: 206,
        58866: 207,
        59869: 208,
        59973: 209,
        60844: 210,
        61535: 211,
        61847: 212,
        62018: 213,
        62122: 214,
        63541: 215,
        63645: 216,
        63853: 217,
        64960: 218,
        65131: 219,
        65859: 220,
        65963: 221,
        66030: 222,
        66134: 223,
        66238: 224,
        66342: 225,
        66446: 226,
        66550: 227,
        66654: 228,
        66758: 229,
        66862: 230,
        67241: 231,
        67969: 232,
        68036: 233,
        68348: 234,
        68452: 235,
        68556: 236,
        68660: 237,
        68764: 238,
        68972: 239,
        69975: 240,
        70014: 241,
        70222: 242,
        70638: 243,
        70742: 244,
        71537: 245,
        71849: 246,
        71953: 247,
        72540: 248,
        72748: 249,
        72852: 250,
        72956: 251,
        73543: 252,
        73647: 253,
        74130: 254,
        101212: 255,
        101628: 256,
        101732: 257,
        102215: 258,
        102319: 259,
        102423: 260,
        102943: 261,
        103114: 262,
        103218: 263,
        103946: 264,
        104221: 265,
        104637: 266,
        104741: 267,
        105120: 268,
        106019: 269,
        106435: 270,
        106747: 271,
        106851: 272,
        106955: 273,
        109132: 274,
        109236: 275,
        109964: 276,
        110003: 277,
        110211: 278,
        110419: 279,
        111838: 280,
        111942: 281,
        112009: 282,
        112113: 283,
        112217: 284,
        112321: 285,
        112841: 286,
        112945: 287,
        113012: 288,
        113428: 289,
        114431: 290,
        114639: 291,
        114951: 292,
        115018: 293,
        115122: 294,
        115226: 295,
        115642: 296,
        115746: 297,
        115850: 298,
        116229: 299,
        117128: 300,
        117232: 301,
        117648: 302,
        117752: 303,
        119030: 304,
        119238: 305,
        119654: 306,
        119862: 307,
        120837: 308,
        120941: 309,
        121424: 310,
        121528: 311,
        121736: 312,
        122115: 313,
        122219: 314,
        122323: 315,
        122427: 316,
        123118: 317,
        123742: 318,
        123846: 319,
        125540: 320,
        125644: 321,
        125748: 322,
        126023: 323,
        126127: 324,
        126335: 325,
        126439: 326,
        126751: 327,
        128133: 328,
        128237: 329,
        129344: 330,
        129448: 331,
        129552: 332,
        129656: 333,
        129864: 334,
        129968: 335,
        130007: 336,
        130111: 337,
        130631: 338,
        130735: 339,
        130839: 340,
        130943: 341,
        131634: 342,
        134851: 343,
        134955: 344,
        135022: 345,
        135126: 346,
        135334: 347,
        135958: 348,
        136233: 349,
        136649: 350,
        137340: 351,
        137444: 352,
        137756: 353,
        137860: 354,
        137964: 355,
        138343: 356,
        138551: 357,
        138863: 358,
        139242: 359,
        139554: 360,
        139970: 361,
        150219: 362,
        150427: 363,
        150531: 364,
        150635: 365,
        150739: 366,
        150843: 367,
        151222: 368,
        151430: 369,
        151534: 370,
        152121: 371,
        153644: 372,
        153748: 373,
        153852: 374,
        153956: 375,
        154023: 376,
        154231: 377,
        154335: 378,
        156237: 379,
        156341: 380,
        157136: 381,
        157240: 382,
        157864: 383,
        158347: 384,
        159350: 385,
        159558: 386,
        159974: 387,
        160117: 388,
        161016: 389,
        161536: 390,
        161640: 391,
        161744: 392,
        162227: 393,
        162435: 394,
        162747: 395,
        162851: 396,
        163022: 397,
        163126: 398,
        163230: 399,
        165028: 400,
        165132: 401,
        165236: 402,
        166239: 403,
        166447: 404,
        167034: 405,
        167554: 406,
        167762: 407,
        168141: 408,
        168245: 409,
        168349: 410,
        168453: 411,
        168661: 412,
        168765: 413,
        169352: 414,
        169456: 415,
        170535: 416,
        171330: 417,
        171434: 418,
        171538: 419,
        172125: 420,
        172957: 421,
        173336: 422,
        173544: 423,
        173648: 424,
        175342: 425,
        175862: 426,
        175966: 427,
        176241: 428,
        176345: 429,
        177140: 430,
        177452: 431,
        178143: 432,
        178455: 433,
        178559: 434,
        179042: 435,
        179146: 436,
        179562: 437,
        179666: 438,
        200106: 439,
        200210: 440,
        200314: 441,
        200418: 442,
        200834: 443,
        200938: 444,
        201525: 445,
        201629: 446,
        201733: 447,
        201837: 448,
        202112: 449,
        202840: 450,
        204222: 451,
        204430: 452,
        204534: 453,
        204638: 454,
        205329: 455,
        205641: 456,
        206332: 457,
        207647: 458,
        207751: 459,
        207855: 460,
        208026: 461,
        208754: 462,
        208962: 463,
        210212: 464,
        210316: 465,
        211319: 466,
        211423: 467,
        211943: 468,
        212114: 469,
        214848: 470,
        214952: 471,
        215019: 472,
        215747: 473,
        215851: 474,
        216126: 475,
        216230: 476,
        216334: 477,
        216646: 478,
        216750: 479,
        216854: 480,
        216958: 481,
        217025: 482,
        217129: 483,
        217753: 484,
        217961: 485,
        219239: 486,
        220734: 487,
        221321: 488,
        221841: 489,
        221945: 490,
        223639: 491,
        223743: 492,
        223847: 493,
        223951: 494,
        224122: 495,
        224226: 496,
        224746: 497,
        224850: 498,
        224954: 499,
        225021: 500,
        225125: 501,
        225229: 502,
        225333: 503,
        225437: 504,
        225541: 505,
        225645: 506,
        225749: 507,
        226024: 508,
        226128: 509,
        226232: 510,
        226648: 511,
        226752: 512,
        226960: 513,
        227027: 514,
        227547: 515,
        227859: 516,
        250220: 517,
        250324: 518,
        250428: 519,
        250532: 520,
        251535: 521,
        251951: 522,
        252330: 523,
        254232: 524,
        254336: 525,
        254960: 526,
        255027: 527,
        255131: 528,
        255651: 529,
        255755: 530,
        256238: 531,
        256342: 532,
        256446: 533,
        259247: 534,
        259559: 535,
        259663: 536,
        260742: 537,
        260950: 538,
        263439: 539,
        264130: 540,
        264234: 541,
        264338: 542,
        264546: 543,
        264650: 544,
        265133: 545,
        265237: 546,
        265549: 547,
        266656: 548,
        266760: 549,
        266864: 550,
        266968: 551,
        267139: 552,
        267347: 553,
        267659: 554,
        267867: 555,
        267971: 556,
        268038: 557,
        268142: 558,
        268246: 559,
        268454: 560,
        268766: 561,
        269041: 562,
        269249: 563,
        269353: 564,
        269457: 565,
        269561: 566,
        269665: 567,
        271019: 568,
        271123: 569,
        271435: 570,
        271643: 571,
        271747: 572,
        272750: 573,
        273545: 574,
        275447: 575,
        275551: 576,
        275655: 577,
        276970: 578,
        277037: 579,
        277141: 580,
        277245: 581,
        277349: 582,
        277557: 583,
        277661: 584,
        277869: 585,
        278040: 586,
        300211: 587,
        300315: 588,
        300627: 589,
        300835: 590,
        300939: 591,
        301006: 592,
        301526: 593,
        301630: 594,
        301734: 595,
        301838: 596,
        302841: 597,
        303116: 598,
        303324: 599,
        303636: 600,
        304639: 601,
        304743: 602,
        304847: 603,
        304951: 604,
        305122: 605,
        306125: 606,
        306333: 607,
        307232: 608,
        307336: 609,
        307440: 610,
        307544: 611,
        307648: 612,
        307752: 613,
        307856: 614,
        308131: 615,
        308235: 616,
        308339: 617,
        308859: 618,
        308963: 619,
        309030: 620,
        309238: 621,
        309342: 622,
        309446: 623,
        310005: 624,
        310213: 625,
        310317: 626,
        312531: 627,
        312739: 628,
        312947: 629,
        313014: 630,
        314121: 631,
        314225: 632,
        314537: 633,
        314641: 634,
        315020: 635,
        315332: 636,
        315436: 637,
        315540: 638,
        316231: 639,
        316959: 640,
        317026: 641,
        317130: 642,
        317234: 643,
        317650: 644,
        318133: 645,
        318861: 646,
        318965: 647,
        319344: 648,
        319448: 649,
        319552: 650,
        319656: 651,
        319760: 652,
        319864: 653,
        320215: 654,
        320319: 655,
        320423: 656,
        320527: 657,
        320631: 658,
        320735: 659,
        320839: 660,
        320943: 661,
        321530: 662,
        321634: 663,
        321738: 664,
        322013: 665,
        322637: 666,
        322741: 667,
        322949: 668,
        323120: 669,
        323328: 670,
        323536: 671,
        324539: 672,
        325022: 673,
        325126: 674,
        325230: 675,
        325334: 676,
        325750: 677,
        325854: 678,
        326025: 679,
        350117: 680,
        350221: 681,
        350429: 682,
        350533: 683,
        350637: 684,
        350845: 685,
        351848: 686,
        352019: 687,
        352851: 688,
        352955: 689,
        353334: 690,
        353438: 691,
        354441: 692,
        354545: 693,
        354649: 694,
        354753: 695,
        354857: 696,
        354961: 697,
        355028: 698,
        355132: 699,
        355340: 700,
        355444: 701,
        355548: 702,
        355756: 703,
        355860: 704,
        355964: 705,
        356031: 706,
        356343: 707,
        356447: 708,
        356551: 709,
        356655: 710,
        356863: 711,
        356967: 712,
        357138: 713,
        357242: 714,
        357346: 715,
        357450: 716,
        357554: 717,
        357658: 718,
        357970: 719,
        358869: 720,
        358973: 721,
        359976: 722,
        360431: 723,
        361746: 724,
        362021: 725,
        362125: 726,
        362229: 727,
        362333: 728,
        362437: 729,
        362541: 730,
        362645: 731,
        362749: 732,
        363232: 733,
        363336: 734,
        363440: 735,
        364235: 736,
        364443: 737,
        364547: 738,
        364963: 739,
        365030: 740,
        365654: 741,
        365862: 742,
        366033: 743,
        366137: 744,
        366241: 745,
        366345: 746,
        366449: 747,
        366553: 748,
        366657: 749,
        367452: 750,
        367556: 751,
        368351: 752,
        368767: 753,
        368871: 754,
        368975: 755,
        369042: 756,
        369146: 757,
        369250: 758,
        369354: 759,
        369874: 760,
        369978: 761,
        370017: 762,
        370121: 763,
        371124: 764,
        371436: 765,
        371540: 766,
        371644: 767,
        371748: 768,
        371956: 769,
        372127: 770,
        372231: 771,
        373130: 772,
        373754: 773,
        400108: 774,
        400836: 775,
        400940: 776,
        401111: 777,
        401215: 778,
        402842: 779,
        402946: 780,
        403429: 781,
        403533: 782,
        403741: 783,
        403845: 784,
        405851: 785,
        406854: 786,
        406958: 787,
        407545: 788,
        409967: 789,
        410422: 790,
        410526: 791,
        410734: 792,
        410942: 793,
        411321: 794,
        411425: 795,
        412012: 796,
        412116: 797,
        412220: 798,
        412948: 799,
        413015: 800,
        413119: 801,
        413327: 802,
        413743: 803,
        413847: 804,
        413951: 805,
        414226: 806,
        414330: 807,
        414434: 808,
        416232: 809,
        416960: 810,
        417131: 811,
        417443: 812,
        418342: 813,
        418862: 814,
        419137: 815,
        419345: 816,
        419449: 817,
        419969: 818,
        420008: 819,
        420320: 820,
        420424: 821,
        420944: 822,
        421011: 823,
        450638: 824,
        451225: 825,
        451329: 826,
        451433: 827,
        451537: 828,
        452020: 829,
        452124: 830,
        453231: 831,
        453335: 832,
        453959: 833,
        454026: 834,
        454650: 835,
        454754: 836,
        455445: 837,
        455549: 838,
        456448: 839,
        456656: 840,
        456760: 841,
        457659: 842,
        457763: 843,
        457867: 844,
        457971: 845,
        458246: 846,
        458454: 847,
        458558: 848,
        458766: 849,
        459353: 850,
        459457: 851,
        459665: 852,
        460224: 853,
        460328: 854,
        460848: 855,
        461227: 856,
        461331: 857,
        461435: 858,
        462438: 859,
        462542: 860,
        462854: 861,
        462958: 862,
        463025: 863,
        463441: 864,
        463545: 865,
        463753: 866,
        463961: 867,
        464340: 868,
        464444: 869,
        465135: 870,
        465239: 871,
        465759: 872,
        465863: 873,
        466034: 874,
        466138: 875,
        466242: 876,
        466346: 877,
        466450: 878,
        466658: 879,
        466970: 880,
        467141: 881,
        467245: 882,
        467349: 883,
        467661: 884,
        468040: 885,
        468872: 886,
        469043: 887,
        469251: 888,
        469355: 889,
        469459: 890,
        469875: 891,
        469979: 892,
        470122: 893,
        471437: 894

    }
    return mapping.get(local_id, "Invalid ID")






def get_global_person_id_a_database_for_human_gait(local_id):
    """
    Returns the global person_ID for a provided local subject_ID of the Database of Human Gait Performance.

    Args:
        local_id (int):
            Local subject_ID of the Database of Human Gait Performance

    Returns:
        (int/string):
            Global person_ID. Returns "Invalid ID" string instead, if subject_ID is unknown.
    """
    mapping = {

        1: 895,
        2: 896,
        3: 897,
        4: 898,
        5: 899,
        6: 900,
        7: 901,
        8: 902,
        9: 903,
        10: 904,
        11: 905,
        12: 906,
        13: 907,
        14: 908,
        15: 909,
        16: 910,
        17: 911,
        18: 912,
        19: 913,
        20: 914,
        21: 915,
        22: 916,
        23: 917,
        24: 918,
        25: 919,
        26: 920,
        27: 921,
        28: 922,
        29: 923,
        30: 924

    }
    return mapping.get(local_id, "Invalid ID")





## ACTIVITY ID

def get_global_activity_id_hugadb(local_id):
    """
    Returns the global Activity_ID for a provided local Activity_ID of the HuGaDB.

    Args:
        local_id (int):
            Local Activity_ID of the HuGaDB

    Returns:
        (int/string):
            Global Activity_ID. Returns "Invalid ID" string instead, if local Activity_ID is unknown.
    """
    mapping = {
        1: 1,
        2: 2,
        3: 5,
        4: 6,
        5: 7,
        6: 8,
        7: 9,
        8: 10,
        9: 11,
        10: 12,
        11: 13,
        12: 14
    }
    return mapping.get(local_id, "Invalid ID")







def get_global_activity_id_ou_isir(local_id):
    """
    Returns the global Activity_ID for a provided local Activity_ID of the OU-ISIR Gait Database.

    Args:
        local_id (int):
            Local Activity_ID of the OU-ISIR Gait Database

    Returns:
        (int/string):
            Global Activity_ID. Returns "Invalid ID" string instead, if local Activity_ID is unknown.
    """
    mapping = {
        -1: 16,
        0: 1,
        1: 5,
        2: 6,
        3: 3,
        4: 4
    }
    return mapping.get(local_id, "Invalid ID")

## GROUND ID






def get_ground_id_by_activity_id_hugabd(activity_ID):
    """
    Returns a Ground_ID for a provided Activity_ID of the HuGaDB.

    Args:
        activity_ID (int):
            Activity_ID of the HuGaDB

    Returns:
        (int/string):
            Ground_ID. Returns "Invalid ID" string instead, if Activity_ID is unknown.
    """
    mapping = {
        1: 1,
        2: 6,
        3: 2,
        4: 3,
        5: 3,
        6: 4,
        7: 4,
        8: 4,
        9: 4,
        10: 4,
        11: 6,
        12: 4,
        13: 4,
        14: 6
    }
    return mapping.get(activity_ID, "Invalid ID")





def get_ground_id_by_activity_id_ou_isir(activity_ID):
    """
    Returns a Ground_ID for a provided Activity_ID of the OU-ISIR Gait Database.

    Args:
        activity_ID (int):
            Activity_ID of the OU-ISIR Gait Database

    Returns:
        (int/string):
            Ground_ID. Returns "Invalid ID" string instead, if Activity_ID is unknown.
    """
    mapping = {
        1: 1,
        3: 2,
        4: 2,
        5: 3,
        6: 3,
        16: 14
    }
    return mapping.get(activity_ID, "Invalid ID")






def get_repetition_by_trial_number(trial_number):
    """
    Returns the repetition for a provided trial number of the Database of Human Gait Performance.

    Args:
        trial_number (int):
            trial_number of the Database of Human Gait Performance

    Returns:
        (int/string):
            The number of recording repetition. Returns "Invalid ID" string instead, if the trial_number is unknown.
    """
    mapping = {

        1: 0,
        2: 1,
        3: 2,
        4: 0,
        5: 1,
        6: 2,
        7: 3,
        8: 4,
        9: 5,
        10: 0,
        11: 1,
        12: 2,
        13: 3,
        14: 4,
        15: 5,
        16: 0,
        17: 0,
        18: 1,
        19: 1,
        20: 2,
        21: 2,
        22: 3,
        23: 3,
        24: 4,
        25: 4,
        26: 5,
        27: 5,
        28: 0,
        29: 0,
        30: 1,
        31: 1,
        32: 2,
        33: 2,
        34: 3,
        35: 3,
        36: 4,
        37: 4,
        38: 5,
        39: 5,
        40: 0,
        41: 0,
        42: 1,
        43: 1, 
        44: 2, 
        45: 2,
        46: 3,
        47: 3,
        48: 4,
        49: 4,
        50: 5,
        51: 5,
        52: 0,
        53: 1,
        54: 2,
        55: 3,
        56: 4,
        57: 5

    }
    return mapping.get(trial_number, "Invalid ID")






def get_activity_id_by_trial_number(trial_number):
    """
    Returns the Activity_ID for a provided trial number of the Database of Human Gait Performance.

    Args:
        trial_number (int):
            trial_number of the Database of Human Gait Performance

    Returns:
        (int/string):
            Activity_ID. Returns "Invalid ID" string instead, if the trial_number is unknown.
    """
    mapping = {

        1: 1,
        2: 1,
        3: 1,
        4: 1,
        5: 1,
        6: 1,
        7: 1,
        8: 1,
        9: 1,
        10: 1,
        11: 1,
        12: 1,
        13: 1,
        14: 1,
        15: 1,
        16: 5,
        17: 6,
        18: 5,
        19: 6,
        20: 5,
        21: 6,
        22: 5,
        23: 6,
        24: 5,
        25: 6,
        26: 5,
        27: 6,
        28: 3,
        29: 4,
        30: 3,
        31: 4,
        32: 3,
        33: 4,
        34: 3,
        35: 4,
        36: 3,
        37: 4,
        38: 3,
        39: 4,
        40: 1,
        41: 1,
        42: 1,
        43: 1, 
        44: 1, 
        45: 1,
        46: 1,
        47: 1,
        48: 1,
        49: 1,
        50: 1,
        51: 1,
        52: 1,
        53: 1,
        54: 1,
        55: 1,
        56: 1,
        57: 1

    }
    return mapping.get(trial_number, "Invalid ID")







def get_ground_id_by_trial_number(trial_number):
    """
    Returns the Ground_ID for a provided trial number of the Database of Human Gait Performance.

    Args:
        trial_number (int):
            trial_number of the Database of Human Gait Performance

    Returns:
        (int/string):
            Ground_ID. Returns "Invalid ID" string instead, if the trial_number is unknown.
    """
    mapping = {

        1: 7,
        2: 7,
        3: 7,
        4: 7,
        5: 7,
        6: 7,
        7: 7,
        8: 7,
        9: 7,
        10: 11,
        11: 11,
        12: 11,
        13: 11,
        14: 11,
        15: 11,
        16: 9,
        17: 9,
        18: 9,
        19: 9,
        20: 9,
        21: 9,
        22: 9,
        23: 9,
        24: 9,
        25: 9,
        26: 9,
        27: 9,
        28: 8,
        29: 8,
        30: 8,
        31: 8,
        32: 8,
        33: 8,
        34: 8,
        35: 8,
        36: 8,
        37: 8,
        38: 8,
        39: 8,
        40: 7,
        41: 7,
        42: 7,
        43: 7, 
        44: 7, 
        45: 7,
        46: 7,
        47: 7,
        48: 7,
        49: 7,
        50: 7,
        51: 7,
        52: 10,
        53: 10,
        54: 10,
        55: 10,
        56: 10,
        57: 10

    }
    return mapping.get(trial_number, "Invalid ID")






def get_sensor_location_id_by_sensor_location_code(sensor_location_code):
    """
    Returns the Sensor_Location_ID for a provided sensor location code of the Database of Human Gait Performance.

    Args:
        sensor_location_code (int):
            Sensor location code of the Database of Human Gait Performance

    Returns:
        (int/string):
            Sensor_Location_ID. Returns "Invalid ID" string instead, if the Sensor location code is unknown.
    """
    mapping = {

        "CC": 26,
        "95": 17,
        "93": 24,
        "8B": 25,
        "9B": 22,
        "B6": 23

    }
    return mapping.get(sensor_location_code, "Invalid ID")




### GLOSSARY (Each function returns the corresponding title to the provided ID)

## GROUND

def get_outside_title(outside_id):
    mapping = {
        0: "Inside",
        1: "Outside",
        2: "Invalid"
    }
    return mapping.get(outside_id, "Invalid ID")

def get_even_slope_stairs_title(even_slope_stairs_id):
    mapping = {
        0: "Even",
        1: "Slope",
        2: "Stairs",
        3: "Others",
        4: "Various",
        5: "Invalid"
    }
    return mapping.get(even_slope_stairs_id, "Invalid ID")



def get_treadmill_title(treadmill_id):
    mapping = {
        0: "Natural",
        1: "Treadmill",
        2: "Invalid"
    }
    return mapping.get(treadmill_id, "Invalid ID")


def get_surface_title(surface_id):
    mapping = {
        0: "Standard Indoor Surface",
        1: "Paved",
        2: "Cement",
        3: "Grass",
        4: "Uneven Stone Brick",
        5: "Various",
        6: "Invalid"
    }
    return mapping.get(surface_id, "Invalid ID")


## RECORDING

def get_dataset_title(dataset_id):
    mapping = {
        0: "Human Gait Database",
        1: "McGill University Gait Database",
        2: "MAREA Gait Database",
        3: "Vajdi Gait Database",
        4: "OU-ISIR Inertial Sensor Dataset 1",
        5: "OU-ISIR Inertial Sensor Dataset 2",
        6: "OU-ISIR Similar Action Inertial Dataset",
        7: "Database of Human Gait Performance"
    }
    return mapping.get(dataset_id, "Invalid ID")


## PERSON

def get_sex_title(sex_id):
    mapping = {
        0: "Male",
        1: "Female"
    }
    return mapping.get(sex_id, "Invalid ID")

def get_smoker_title(smoker_id):
    mapping = {
        0: "Non-Smoker",
        1: "Smoker"
    }
    return mapping.get(smoker_id, "Invalid ID")



## SENSOR


def get_sensor_modality_title(sensor_id):
    mapping = {
        0: "Accelerometer",
        1: "Gyroscope",
        2: "EMG",
        3: "Magnetometer"
    }
    return mapping.get(sensor_id, "Invalid ID")

def get_sensor_type_title(packaging_id):
    mapping = {
        0: "Inertial Measurement Unit",
        1: "Smartphone Sensor",
        2: "Standalone EMG"
    }
    return mapping.get(packaging_id, "Invalid ID")

def get_internal_coordinate_system_title(internal_coordinate_system_id):
    mapping = {
        0: "x right, y superior, z anterior", # HuGADB (gyroscope & accelerometer), McGill, MAREA, ISIR1+2+SAID
        1: "x superior, y left, z anterior", # OU-ISIR (Smartphone), A database for human gait
        2: "x right, y anterior, z superior", # Vajdi
    }
    return mapping.get(internal_coordinate_system_id, "Invalid ID")
    

## ACTIVITY

def get_activity_type_title(activity_type_id):
    mapping = {
        0: "Active Walking",
        1: "Active Other",
        2: "Passive",
        3: "Invalid",
        4: "Mixed"
    }
    return mapping.get(activity_type_id, "Invalid ID")


def get_activity_name_title(activity_name_id):
    mapping = {
        0: "Walking",
        1: "Running",
        2: "Going slope up",
        3: "Going slope down",
        4: "Going stairs up",
        5: "Going stairs down",
        6: "Sitting",
        7: "Sitting down",
        8: "Standing up",
        9: "Standing",
        10: "Bicycling",
        11: "Up by elevator",
        12: "Down by elevator",
        13: "Sitting in car",
        14: "Walking & Running",
        15: "Invalid",
        16: "Mixed"
    }
    return mapping.get(activity_name_id, "Invalid ID")



## SENSOR_LOCATION

def get_body_side_title(body_side_id):
    mapping = {
        0: "Right",
        1: "Center",
        2: "Left"
    }
    return mapping.get(body_side_id, "Invalid ID")

def get_body_area_title(body_area_id):
    mapping = {
        0: "Foot",
        1: "Ankle",
        2: "Shin",
        3: "Thigh",
        4: "Pocket",
        5: "Waist",
        6: "Wrist"
    }
    return mapping.get(body_area_id, "Invalid ID")

def get_position_title(position_id):
    mapping = {
        0: "Top of left foot",
        1: "Top of right foot",
        2: "Left ankle",
        3: "Right ankle",
        4: "Left shin",
        5: "Right shin",
        6: "Left thigh front",
        7: "Right thigh front",
        8: "Left vastus lateralis",
        9: "Right vastus lateralis",
        10: "Left front pocket",
        11: "Left back pocket",
        12: "Right front pocket",
        13: "Center waist back",
        14: "Left waist",
        15: "Right waist",
        16: "Center waist front",
        17: "Left wrist",
        18: "Right wrist"
    }
    return mapping.get(position_id, "Invalid ID")


## WORLD_COORDINATE_SYSTEM

def get_alignment_title(alignment_id):
    mapping = {
        0: "x superior, y right, z posterior", #HuGaDB "normal"
        1: "x posterior, y right, z inferior", #HuGaDB Foot
        2: "x right, y inferior, z posterior", #McGill front pockets
        3: "x left, y inferior, z anterior",    #McGill back pocket, MAREA waist front center
        4: "x anterior, y superior, z left", #OU-ISIR left waist
        5: "x left, y superior, z posterior", #OU-ISIR center back
        6: "x superior, y right, z posterior", #OU-ISIR center back (smartphone)
        7: "x posterior, y superior, z right", #OU-ISIR right waist
        8: "x superior, y left, z anterior", #DBHuGa Thigh and Shin
        9: "x superior, y right, z posterior", #DBHuGa Center Back
        10: "x superior, y posterior, z left", #DBHuGa left Wrist
        11: "x anterior, y inferior, z right", #MAREA - right wrist, right ankle
        12: "x posterior, y inferior, z left", #MAREA - left ankle
        13: "x right, y posterior, z inferior", #Vajdi left Front Pocket
        14: "x posterior, y left, z inferior" #Vajdi right Waist
    }
    return mapping.get(alignment_id, "Invalid ID")


## STEP_EVENT

def get_ground_truth_event_title(ground_truth_event_id):
    mapping = {
        0: "No Event",
        1: "Toe-Off Event Left",
        2: "Toe-Off Event Right",
        3: "Heel-Strike Event Left",
        4: "Heel-Strike Event Right"
    }
    return mapping.get(ground_truth_event_id, "Invalid ID")


def get_ground_truth_event_id_by_abbreviation(ground_truth_event_abbreviation):
    mapping = {
        "rf_to": 1,
        "lf_to": 2,
        "rf_hs": 3,
        "lf_hs": 4
    }
    return mapping.get(ground_truth_event_abbreviation, "Invalid ID")


def get_detected_event_title(detected_event_id):
    mapping = {
        0: "No Event",
        1: "Dominant Peak",
        2: "Non-Dominant Peak",
        3: "Minimum"
    }
    return mapping.get(detected_event_id, "Invalid ID")