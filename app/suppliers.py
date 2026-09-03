from dataclasses import dataclass


def normalize_supplier_code(value: str) -> str:
    normalized = value.strip().upper().replace(" ", "-")
    if not normalized:
        raise ValueError("supplier code is required")
    if len(normalized) > 32:
        raise ValueError("supplier code cannot exceed 32 characters")
    if not all(character.isalnum() or character in {"-", "_"} for character in normalized):
        raise ValueError("supplier code contains unsupported characters")
    return normalized


@dataclass(frozen=True, slots=True)
class Supplier:
    code: str
    name: str
    email: str | None = None
    phone: str | None = None
    active: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "code", normalize_supplier_code(self.code))
        object.__setattr__(self, "name", self.name.strip())
        object.__setattr__(self, "email", self.email.strip().lower() if self.email else None)
        object.__setattr__(self, "phone", self.phone.strip() if self.phone else None)
        if not self.name:
            raise ValueError("supplier name is required")
        if self.email:
            local, separator, domain = self.email.partition("@")
            if not local or separator != "@" or "." not in domain:
                raise ValueError("supplier email is invalid")
        if self.phone and not all(character.isdigit() or character in "+- ()" for character in self.phone):
            raise ValueError("supplier phone is invalid")
        if not self.email and not self.phone:
            raise ValueError("supplier email or phone is required")
