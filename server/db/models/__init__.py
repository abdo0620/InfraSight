from db.models.core import Ticket, TicketEvent, TicketFallback, Upload, User  # noqa: F401
from db.models.admin import Department, SlaPolicy, TicketAdmin, UnclassifiedQueue  # noqa: F401
from db.models.compliance import (  # noqa: F401
    Jurisdiction, TicketCompliance, TicketPermitCheck, TicketSopDocument, TicketUtilityAlert,
)
