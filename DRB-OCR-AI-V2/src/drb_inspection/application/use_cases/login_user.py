from __future__ import annotations

from dataclasses import dataclass, replace

from drb_inspection.adapters.db.base import RepositoryAdapter
from drb_inspection.application.contracts.context import LoginCommand, LoginResult


@dataclass
class LoginUserUseCase:
    repository: RepositoryAdapter

    def execute(self, command: LoginCommand) -> LoginResult:
        user_name = command.user_name.strip()
        password = command.password.strip()
        if not user_name or not password:
            return LoginResult(success=False, message="Please enter UserName and Password!")

        user = self.repository.get_user(user_name)
        if user is None:
            return LoginResult(success=False, message="UserName does not exist! Please try again.")

        if user.active != "Active":
            return LoginResult(
                success=False,
                message="UserName is inactive or locked! Please contact Administrator to activate.",
                user=user,
            )

        if user.password_hash != password:
            attempt = user.attempt + 1
            if user.role != "Administrator" and attempt >= 3:
                locked_user = replace(user, attempt=attempt, active="Inactive")
                self.repository.save_user(locked_user)
                return LoginResult(
                    success=False,
                    message="UserName locked after 3 failed attempts!",
                    user=locked_user,
                )

            updated_user = replace(user, attempt=attempt)
            self.repository.save_user(updated_user)
            return LoginResult(
                success=False,
                message="Password is incorrect!",
                user=updated_user,
            )

        authenticated_user = replace(user, attempt=0)
        self.repository.save_user(authenticated_user)
        session = self.repository.update_session(user_name=authenticated_user.user_name)
        self.repository.record_event(f"Login success user={authenticated_user.user_name}")
        return LoginResult(
            success=True,
            message="Login success.",
            user=authenticated_user,
            session=session,
        )
