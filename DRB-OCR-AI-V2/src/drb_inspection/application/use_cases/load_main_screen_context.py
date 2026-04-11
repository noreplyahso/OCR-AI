from __future__ import annotations

from dataclasses import dataclass

from drb_inspection.adapters.db.base import RepositoryAdapter
from drb_inspection.application.contracts.context import MainScreenContext
from drb_inspection.application.use_cases.get_access_profile import GetAccessProfileUseCase


@dataclass
class LoadMainScreenContextUseCase:
    repository: RepositoryAdapter
    get_access_profile: GetAccessProfileUseCase

    def execute(self) -> MainScreenContext:
        session = self.repository.get_session()
        user = self.repository.get_user(session.user_name) if session.user_name else None
        role = user.role if user and user.role else "Operator"
        access_profile = self.get_access_profile.execute(role=role)
        available_products = [product.product_name for product in self.repository.list_products()]
        selected_product = self.repository.get_product(session.product_name) if session.product_name else None
        recent_history = self.repository.list_recent_inspection_history(limit=10)
        self.repository.record_event(
            f"Load main screen context user={session.user_name or ''} role={role} products={len(available_products)}"
        )
        return MainScreenContext(
            current_user_name=session.user_name,
            current_role=role,
            session=session,
            available_products=available_products,
            recent_inspection_history=recent_history,
            selected_model_path=selected_product.model_path if selected_product else "",
            selected_product=selected_product,
            access_profile=access_profile,
        )
