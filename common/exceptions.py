# common/exceptions.py
from dataclasses import dataclass, field
from typing import Optional, Tuple
from common.constants import (
    EXCEPTION_CODE_BASE,
    ELEMENT_NOT_FOUND_CODE,
    ELEMENT_NOT_CLICKABLE_CODE,
    ELEMENT_INPUT_FAILED_CODE,
    PAGE_SWITCH_FAILED_CODE,
    DRIVER_INIT_FAILED_CODE,
    DEVICE_OPERATION_FAILED_CODE,
)


@dataclass
class BaseAppiumException(Exception):
    code: str = EXCEPTION_CODE_BASE
    message: str = "Unknown error"
    locator: Optional[Tuple] = None
    page: Optional[str] = None
    action: Optional[str] = None
    extra: dict = field(default_factory=dict)

    def __post_init__(self):
        super().__init__(self.__str__())

    def __str__(self) -> str:
        msg = f"[{self.code}] {self.message}"
        if self.page:
            msg += f" | Page: {self.page}"
        if self.action:
            msg += f" | Action: {self.action}"
        if self.locator:
            msg += f" | Locator: {self.locator}"
        if self.extra:
            msg += f" | Extra: {self.extra}"
        return msg


@dataclass
class ElementNotFoundException(BaseAppiumException):
    code: str = ELEMENT_NOT_FOUND_CODE
    message: str = "Element not found within timeout"


@dataclass
class ElementNotClickableException(BaseAppiumException):
    code: str = ELEMENT_NOT_CLICKABLE_CODE
    message: str = "Element exists but not clickable"


@dataclass
class ElementInputException(BaseAppiumException):
    code: str = ELEMENT_INPUT_FAILED_CODE
    message: str = "Failed to input text into element"


@dataclass
class PageSwitchFailedException(BaseAppiumException):
    code: str = PAGE_SWITCH_FAILED_CODE
    message: str = "Page switch failed"


@dataclass
class DriverInitException(BaseAppiumException):
    code: str = DRIVER_INIT_FAILED_CODE
    message: str = "Appium driver initialization failed"


@dataclass
class DeviceOperationException(BaseAppiumException):
    code: str = DEVICE_OPERATION_FAILED_CODE
    message: str = "Device operation failed"