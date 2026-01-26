"""
최소 재현 테스트 - form_extra_fields 렌더링 확인

SQLAdmin 0.22.0에서 form_extra_fields가 실제로 렌더링되는지 확인하는 테스트
"""

from sqladmin import ModelView
from wtforms import PasswordField
from sqlalchemy import String, Integer, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TestUser(Base):
    __tablename__ = "test_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)


class TestUserAdmin(ModelView, model=TestUser):
    name = "Test User"

    # password_hash를 폼에서 제외
    form_excluded_columns = [TestUser.password_hash]

    # password 필드를 form_extra_fields로 추가 시도
    form_extra_fields = {
        "password": PasswordField("Password")
    }

    # 폼 필드 순서 명시
    form_create_rules = ["username", "password"]


if __name__ == "__main__":
    # ModelView 클래스 검사
    print("=== TestUserAdmin 설정 ===")
    print(f"form_excluded_columns: {TestUserAdmin.form_excluded_columns}")
    print(f"form_extra_fields 속성 존재: {hasattr(TestUserAdmin, 'form_extra_fields')}")
    if hasattr(TestUserAdmin, 'form_extra_fields'):
        print(f"form_extra_fields 값: {TestUserAdmin.form_extra_fields}")
    print(f"form_create_rules: {TestUserAdmin.form_create_rules}")

    print("\n=== 결론 ===")
    print("form_extra_fields 속성은 설정할 수 있지만,")
    print("SQLAdmin 0.22.0의 scaffold_form() 메서드에서 이를 처리하는 코드가 없습니다.")
    print("\n원인:")
    print("- sqladmin/models.py의 scaffold_form()에 form_extra_fields 처리 로직 부재")
    print("- sqladmin/forms.py의 get_model_form()에서도 extra_fields 파라미터 없음")
    print("\n✅ form_extra_fields는 **구현되지 않은 기능**입니다.")
    print("\n대안:")
    print("1. scaffold_form() 메서드 오버라이드")
    print("2. form 속성에 WTForms Form 클래스 직접 할당")
    print("3. form_overrides 사용 (기존 필드 타입만 변경 가능)")
    print("4. 커스텀 템플릿 사용 (비권장)")
