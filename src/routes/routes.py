from src.controller.main_controller import *
from src.controller.error_controller import *
from src.controller.login_controller import LoginController
from src.controller.register_controller import RegisterController
from src.controller.dashboard_controller import DashboardController
from src.controller.logout_controller import LogoutController
from src.controller.admin_controller import AdminController
from src.controller.maintenance_controller import MaintenanceController

routes = {
    "main_route": "/", "main_controller": MainController.as_view("controle principal"),
    "login_route": "/login", "login_controller": LoginController.as_view("controle login"),
    "dashboard_route": "/dashboard", "dashboard_controller": DashboardController.as_view("controle dashboard"),
    "logout_route": "/logout", "logout_controller": LogoutController.as_view("controle logout"),
    "admin_route": "/admin", "admin_controller": AdminController.as_view("controle admin"),
    "maintenance_route": "/maintenance", "maintenance_controller": MaintenanceController.as_view("controle manutencao"),
}