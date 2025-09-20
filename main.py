import os
import shutil
import time
from pathlib import Path
from sqlmodel import SQLModel, Field, Session, create_engine, select

# 定义 User 表结构
class User(SQLModel, table=True):
    userid: str = Field(primary_key=True)
    UserName: str
    LastTime: int
    Password: str
    UserKey: str


def add_user_from_images(image_folder: str):
    username = os.getlogin()
    roaming = Path(os.environ["APPDATA"])
    db_path = roaming / "Seewo" / "Users" / "User.db"
    data_root = roaming / "Seewo" / "EasiNote5" / "Data"

    # Configs 模板路径
    configs_template = Path("./Configs.fkv")
    if not configs_template.exists():
        raise FileNotFoundError("❌ 没有找到 ./Configs.fkv 模板文件")

    # 连接数据库
    engine = create_engine(f"sqlite:///{db_path}", echo=False)

    with Session(engine) as session:
        # 获取已有 userid
        result = session.exec(select(User.userid)).all()
        existing_ids = set(result)

        # 遍历图片
        for img_file in Path(image_folder).glob("*.*"):
            if img_file.suffix.lower() not in [".jpg", ".jpeg", ".png", ".bmp", ".gif"]:
                continue

            userid = img_file.stem  # 图片名作为 userid
            username_from_img = img_file.stem
            last_time_ms = int(time.time() * 1000) + 10**12  # 未来时间，毫秒级

            if userid not in existing_ids:
                # 插入新用户
                new_user = User(
                    userid=userid,
                    UserName=username_from_img,
                    LastTime=last_time_ms,
                    Password="1145114",
                    UserKey="114514"
                )
                session.add(new_user)
                session.commit()
                existing_ids.add(userid)
                print(f"✅ 添加数据库用户 {userid}，用户名 {username_from_img}")
            else:
                # 用户已存在 → 更新 LastTime
                user = session.get(User, userid)
                if user:
                    user.LastTime = last_time_ms
                    session.add(user)
                    session.commit()
                    print(f"🔄 更新用户 {userid} 的 LastTime")

            # 创建目录并复制文件
            target_dir = data_root / userid
            target_dir.mkdir(parents=True, exist_ok=True)
            target_img_path = target_dir / img_file.name
            shutil.copy(img_file, target_img_path)

            # 修改 Configs.fkv
            configs_text = configs_template.read_text(encoding="utf-8")
            configs_text = configs_text.replace(
                "UserPhoto.Photo\npath",
                f"UserPhoto.Photo\n{target_img_path}"
            )
            (target_dir / "Configs.fkv").write_text(configs_text, encoding="utf-8")

            print(f"✅ 复制图片 {img_file.name} 并生成 Configs.fkv 到 {target_dir}")


if __name__ == "__main__":
    image_folder = r"./targets"  # TODO: 修改为图片路径
    add_user_from_images(image_folder)
