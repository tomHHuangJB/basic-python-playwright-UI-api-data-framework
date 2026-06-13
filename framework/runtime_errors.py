from dataclasses import dataclass, field

# For AI-generated apps, a page that visually loads can still be broken. I collect console errors,
# page exceptions, and failed network requests as runtime quality signals.

@dataclass
class RuntimeErrors:
    console_errors: list[str] = field(default_factory=list)  # Creates a new empty list for each RuntimeErrors instance.
    page_errors: list[str] = field(default_factory=list)  # Avoids sharing one mutable list across all instances.
    failed_requests: list[str] = field(default_factory=list)  # Stores failed requests in this instance's own list.

    def has_errors(self) -> bool:
        return bool(self.console_errors or self.page_errors or self.failed_requests)

    def summary(self) -> dict[str, list[str]]:
        return {
            "console-errors": self.console_errors,
            "page_errors": self.page_errors,
            "failed_requests": self.failed_requests,
        }


