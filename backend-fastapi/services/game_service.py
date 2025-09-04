import datetime, random
from services.firebase_service import db
from firebase_admin import firestore

STAR_TYPES = ["blue_giant", "red_dwarf", "yellow_star", "white_dwarf", "neutron_star"]

def get_today():
    return datetime.datetime.now().strftime("%Y-%m-%d")

def get_week_id(date_str):
    date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    week_num = (date.day - 1) // 7 + 1
    return f"{date.year}-{date.month:02d}-w{week_num}"

def checkin_and_give_star(user_id: str, today: str):
    star_ref = db.collection("users").document(user_id).collection("star_systems").document(today)
    if star_ref.get().exists:
        return {"already_checked_in": True}

    star = random.choice(STAR_TYPES)
    star_ref.set({
        "star": star,
        "planets": [],
        "timestamp": firestore.SERVER_TIMESTAMP
    })

    # 주간 energy += 1
    week_id = get_week_id(today)
    cluster_ref = db.collection("users").document(user_id).collection("clusters").document(week_id)
    cluster_ref.set({"energy": firestore.Increment(1)}, merge=True)

    return {"star": star}

def record_action(user_id: str, today: str, action_type: str):
    star_ref = db.collection("users").document(user_id).collection("star_systems").document(today)
    doc = star_ref.get()

    if not doc.exists:
        return {"error": "오늘 접속 보상을 먼저 받아야 해요!"}

    data = doc.to_dict()
    planets = data.get("planets", [])

    found = False
    for planet in planets:
        if planet["type"] == action_type:
            planet["level"] += 1
            found = True
            break

    if not found:
        planets.append({"type": action_type, "level": 1})

    star_ref.update({"planets": planets})

    return {
        "message": "행성 추가 완료!" if not found else "행성 업그레이드 완료!",
        "planets": planets
    }

def get_full_galaxy(user_id: str, month: str):
    galaxy = {"clusters": []}

    # 최대 5주차까지 확인
    for week_num in range(1, 6):
        week_id = f"{month}-w{week_num}"
        cluster_ref = db.collection("users").document(user_id).collection("clusters").document(week_id)
        cluster_doc = cluster_ref.get()

        if not cluster_doc.exists:
            continue

        cluster_data = cluster_doc.to_dict()

        # 날짜 계산: 해당 주차의 1일~7일 범위 추정
        start_day = (week_num - 1) * 7 + 1
        end_day = min(start_day + 6, 31)  # 최대 31일

        star_systems = []
        for day in range(start_day, end_day + 1):
            date_str = f"{month}-{day:02d}"
            star_ref = db.collection("users").document(user_id).collection("star_systems").document(date_str)
            star_doc = star_ref.get()
            if star_doc.exists:
                star_data = star_doc.to_dict()
                star_systems.append({
                    "date": date_str,
                    "star": star_data.get("star"),
                    "planets": star_data.get("planets", [])
                })

        galaxy["clusters"].append({
            "week": week_id,
            "energy": cluster_data.get("energy", 0),
            "reward": cluster_data.get("reward", None),
            "star_systems": star_systems
        })

    return galaxy