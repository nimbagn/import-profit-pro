# models.py
# Modèles SQLAlchemy pour Import Profit Pro

from __future__ import annotations

from datetime import datetime, date, UTC
from decimal import Decimal
from typing import Optional

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy.dialects import mysql

db = SQLAlchemy()

# -------- Types numériques --------
N18_2 = db.Numeric(18, 2)
N18_4 = db.Numeric(18, 4)

# BIGINT UNSIGNED côté MySQL, BigInteger générique ailleurs
BIGINT_U = db.BigInteger().with_variant(mysql.BIGINT(unsigned=True), "mysql")

# Helper pour PK & FK
def PK():
    return db.Column(BIGINT_U, primary_key=True)

def FK(ref: str, nullable=True, **kwargs):
    """Créer une ForeignKey avec BIGINT UNSIGNED"""
    fk_kwargs = {k: v for k, v in kwargs.items() if k.startswith('on')}
    col_kwargs = {k: v for k, v in kwargs.items() if not k.startswith('on')}
    return db.Column(BIGINT_U, db.ForeignKey(ref, **fk_kwargs), nullable=nullable, **col_kwargs)

# =========================================================
# IMPORT PROFIT PRO — CATEGORIES / ARTICLES / SIMULATIONS
# =========================================================

class Category(db.Model):
    __tablename__ = "categories"
    id = PK()
    name = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(UTC))

    def __repr__(self):
        return f"<Category {self.name}>"

class Article(db.Model):
    __tablename__ = "articles"
    id = PK()
    name = db.Column(db.String(160), unique=True, nullable=False)
    category_id = FK("categories.id", onupdate="CASCADE", ondelete="RESTRICT")

    purchase_price = db.Column(N18_4, nullable=False, default=Decimal("0.0000"))
    purchase_currency = db.Column(db.String(8), nullable=False, default="USD")
    unit_weight_kg = db.Column(N18_4, nullable=False, default=Decimal("0.0000"))
    image_path = db.Column(db.String(500), nullable=True)  # Chemin relatif vers l'image dans instance/uploads/articles/

    is_active = db.Column(db.Boolean, nullable=False, default=True)

    category = db.relationship("Category", backref=db.backref("articles", lazy="select"))

    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(UTC))

    __table_args__ = (
        db.Index("idx_article_name", "name"),
        db.Index("idx_article_category", "category_id"),
    )

    def __repr__(self):
        return f"<Article {self.name}>"

class Simulation(db.Model):
    __tablename__ = "simulations"
    id = PK()

    rate_usd = db.Column(N18_4, nullable=False, default=Decimal("0"))
    rate_eur = db.Column(N18_4, nullable=False, default=Decimal("0"))
    rate_xof = db.Column(N18_4, nullable=False, default=Decimal("0"))

    customs_gnf = db.Column(N18_2, nullable=False, default=Decimal("0.00"))
    handling_gnf = db.Column(N18_2, nullable=False, default=Decimal("0.00"))
    others_gnf = db.Column(N18_2, nullable=False, default=Decimal("0.00"))
    transport_fixed_gnf = db.Column(N18_2, nullable=False, default=Decimal("0.00"))
    transport_per_kg_gnf = db.Column(N18_4, nullable=False, default=Decimal("0.0000"))

    basis = db.Column(db.Enum("value", "weight", name="sim_basis"), nullable=False, default="value")
    truck_capacity_tons = db.Column(N18_4, nullable=False, default=Decimal("0.0000"))

    target_mode = db.Column(db.Enum("none", "price", "purchase", "global", name="sim_target_mode"),
                            nullable=False, default="none")
    target_margin_pct = db.Column(N18_4, nullable=False, default=Decimal("0.0000"))

    is_completed = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC), index=True)
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(UTC))

    items = db.relationship("SimulationItem", backref="simulation",
                            cascade="all, delete-orphan", lazy="selectin")

    def __repr__(self):
        return f"<Simulation {self.id}>"

class SimulationItem(db.Model):
    __tablename__ = "simulation_items"
    id = PK()
    simulation_id = FK("simulations.id", onupdate="CASCADE", ondelete="CASCADE")
    article_id = FK("articles.id", onupdate="CASCADE", ondelete="RESTRICT")

    quantity = db.Column(N18_4, nullable=False, default=Decimal("0.0000"))
    selling_price_gnf = db.Column(N18_2, nullable=False, default=Decimal("0.00"))

    purchase_price = db.Column(N18_4, nullable=False, default=Decimal("0.0000"))
    purchase_currency = db.Column(db.String(8), nullable=False, default="USD")
    unit_weight_kg = db.Column(N18_4, nullable=False, default=Decimal("0.0000"))

    article = db.relationship("Article", lazy="joined")

    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))

    __table_args__ = (
        db.UniqueConstraint("simulation_id", "article_id", name="uq_sim_item"),
        db.Index("idx_simitem_sim", "simulation_id"),
        db.Index("idx_simitem_article", "article_id"),
    )

    def __repr__(self):
        return f"<SimulationItem sim={self.simulation_id} art={self.article_id} qty={self.quantity}>"

    @property
    def margin_pct(self):
        """Calculer le pourcentage de marge"""
        if self.selling_price_gnf and self.purchase_price:
            cost_gnf = float(self.purchase_price) * 8500  # Taux USD fixe pour l'exemple
            if cost_gnf > 0:
                return ((float(self.selling_price_gnf) - cost_gnf) / cost_gnf) * 100
        return 0

# =========================================================
# AUTHENTIFICATION — RÔLES / UTILISATEURS (DOIT ÊTRE AVANT VEHICLE)
# =========================================================

class Role(db.Model):
    __tablename__ = "roles"
    id = PK()
    name = db.Column(db.String(50), unique=True, nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    permissions = db.Column(db.JSON, nullable=True)  # JSON simple pour les permissions
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(UTC))
    
    users = db.relationship("User", backref="role", lazy="select")
    
    __table_args__ = (
        db.Index("idx_role_code", "code"),
    )
    
    def __repr__(self):
        return f"<Role {self.name}>"

class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = PK()
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    role_id = FK("roles.id", onupdate="CASCADE", ondelete="RESTRICT")
    region_id = FK("regions.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    last_login = db.Column(db.DateTime, nullable=True)
    additional_permissions = db.Column(db.JSON, nullable=True)  # Permissions supplémentaires (ex: stocks.read pour RH)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(UTC))
    
    movements = db.relationship("StockMovement", backref="user", lazy="dynamic")
    # Note: inventory_sessions relation is defined via back_populates in InventorySession
    
    __table_args__ = (
        db.Index("idx_user_username", "username"),
        db.Index("idx_user_email", "email"),
        db.Index("idx_user_role", "role_id"),
        db.Index("idx_user_region", "region_id"),
    )
    
    def __repr__(self):
        return f"<User {self.username}>"
    
    # Relation avec UserPreference
    preference = db.relationship("UserPreference", backref="user", uselist=False, cascade="all, delete-orphan")
    
    # Relation avec PasswordResetToken
    password_reset_tokens = db.relationship("PasswordResetToken", backref="user", lazy="dynamic", cascade="all, delete-orphan")

class PasswordResetToken(db.Model):
    """Token de réinitialisation de mot de passe"""
    __tablename__ = "password_reset_tokens"
    id = PK()
    user_id = FK("users.id", onupdate="CASCADE", ondelete="CASCADE", nullable=False)
    token_hash = db.Column(db.String(255), nullable=False, unique=True, index=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    used = db.Column(db.Boolean, nullable=False, default=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(UTC))
    
    __table_args__ = (
        db.Index("idx_reset_token_hash", "token_hash"),
        db.Index("idx_reset_token_expires", "expires_at"),
        db.Index("idx_reset_token_user", "user_id"),
    )
    
    def __repr__(self):
        return f"<PasswordResetToken user_id={self.user_id} expires_at={self.expires_at} used={self.used}>"
    
    def is_valid(self):
        """Vérifier si le token est valide (non expiré et non utilisé)"""
        from datetime import datetime, UTC
        return not self.used and self.expires_at > datetime.now(UTC)

class UserPreference(db.Model):
    """Préférences utilisateur pour les thèmes et l'apparence"""
    __tablename__ = "user_preferences"
    id = PK()
    user_id = FK("users.id", onupdate="CASCADE", ondelete="CASCADE", nullable=False, unique=True)
    theme_name = db.Column(db.String(50), nullable=False, default="hapag-lloyd")  # hapag-lloyd, professional, energetic, nature, dark
    color_mode = db.Column(db.String(20), nullable=False, default="light")  # light, dark
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(UTC))
    
    __table_args__ = (
        db.Index("idx_user_pref_user", "user_id"),
    )
    
    def __repr__(self):
        return f"<UserPreference user={self.user_id} theme={self.theme_name} mode={self.color_mode}>"

class UserActivityLog(db.Model):
    """Journal des activités et interactions des utilisateurs"""
    __tablename__ = "user_activity_logs"
    id = PK()
    user_id = FK("users.id", onupdate="CASCADE", ondelete="CASCADE", nullable=False, index=True)
    action = db.Column(db.String(100), nullable=False, index=True)  # login, logout, create_order, update_stock, etc.
    module = db.Column(db.String(50), nullable=True, index=True)  # auth, orders, stocks, etc.
    activity_metadata = db.Column(db.JSON, nullable=True)  # Données additionnelles (JSON) - renommé de 'metadata' car réservé par SQLAlchemy
    ip_address = db.Column(db.String(45), nullable=True)  # IPv4 ou IPv6
    user_agent = db.Column(db.String(500), nullable=True)  # User-Agent du navigateur
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC), index=True)
    
    user = db.relationship("User", backref=db.backref("activity_logs", lazy="dynamic"))
    
    __table_args__ = (
        db.Index("idx_activity_user", "user_id"),
        db.Index("idx_activity_action", "action"),
        db.Index("idx_activity_module", "module"),
        db.Index("idx_activity_created", "created_at"),
        db.Index("idx_activity_user_action", "user_id", "action"),
    )
    
    def __repr__(self):
        return f"<UserActivityLog user={self.user_id} action={self.action} at={self.created_at}>"

# =========================================================
# RESSOURCES HUMAINES — EMPLOYÉS EXTERNES (SANS ACCÈS PLATEFORME)
# =========================================================

class Employee(db.Model):
    """Employés sans accès à la plateforme mais suivis par le service RH"""
    __tablename__ = "employees"
    id = PK()
    employee_number = db.Column(db.String(50), unique=True, nullable=False, index=True)  # Numéro d'employé
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    phone_secondary = db.Column(db.String(20), nullable=True)
    gender = db.Column(db.Enum("M", "F", name="gender"), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    national_id = db.Column(db.String(50), nullable=True, index=True)  # Numéro CNI/Passeport
    address = db.Column(db.String(500), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    emergency_contact_name = db.Column(db.String(200), nullable=True)
    emergency_contact_phone = db.Column(db.String(20), nullable=True)
    emergency_contact_relation = db.Column(db.String(50), nullable=True)  # Relation (conjoint, parent, etc.)
    
    # Informations professionnelles
    department = db.Column(db.String(100), nullable=True)  # Département/Service
    position = db.Column(db.String(100), nullable=True)  # Poste/Fonction
    manager_id = FK("employees.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")  # Responsable hiérarchique
    region_id = FK("regions.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")
    depot_id = FK("depots.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")
    
    # Statut
    employment_status = db.Column(db.Enum("active", "inactive", "suspended", "terminated", "on_leave", name="employment_status"), 
                                 nullable=False, default="active", index=True)
    hire_date = db.Column(db.Date, nullable=True, index=True)  # Date d'embauche
    termination_date = db.Column(db.Date, nullable=True)  # Date de fin de contrat
    termination_reason = db.Column(db.Text, nullable=True)  # Raison de fin de contrat
    
    # Lien avec utilisateur (si l'employé a un compte)
    user_id = FK("users.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL", unique=True)
    
    # Métadonnées
    notes = db.Column(db.Text, nullable=True)  # Notes générales
    photo_path = db.Column(db.String(500), nullable=True)  # Photo de profil
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(UTC))
    created_by_id = FK("users.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")
    
    # Relations
    manager = db.relationship("Employee", remote_side=[id], backref="subordinates")
    region = db.relationship("Region", backref="employees")
    depot = db.relationship("Depot", backref="employees")
    user = db.relationship("User", foreign_keys=[user_id], backref="employee_profile")
    created_by = db.relationship("User", foreign_keys=[created_by_id], backref="created_employees")
    contracts = db.relationship("EmployeeContract", backref="employee", lazy="dynamic", cascade="all, delete-orphan", order_by="desc(EmployeeContract.start_date)")
    trainings = db.relationship("EmployeeTraining", backref="employee", lazy="dynamic", cascade="all, delete-orphan", order_by="desc(EmployeeTraining.start_date)")
    evaluations = db.relationship("EmployeeEvaluation", backref="employee", lazy="dynamic", cascade="all, delete-orphan", order_by="desc(EmployeeEvaluation.evaluation_date)")
    absences = db.relationship("EmployeeAbsence", backref="employee", lazy="dynamic", cascade="all, delete-orphan", order_by="desc(EmployeeAbsence.start_date)")
    
    __table_args__ = (
        db.Index("idx_employee_number", "employee_number"),
        db.Index("idx_employee_name", "last_name", "first_name"),
        db.Index("idx_employee_status", "employment_status"),
        db.Index("idx_employee_department", "department"),
        db.Index("idx_employee_position", "position"),
    )
    
    @property
    def full_name(self):
        """Nom complet de l'employé"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def current_contract(self):
        """Contrat actuel (le plus récent actif)"""
        return self.contracts.filter_by(status='active').first()
    
    def __repr__(self):
        return f"<Employee {self.employee_number} - {self.full_name}>"

class EmployeeContract(db.Model):
    """Contrats des employés"""
    __tablename__ = "employee_contracts"
    id = PK()
    employee_id = FK("employees.id", nullable=False, onupdate="CASCADE", ondelete="CASCADE", index=True)
    contract_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    contract_type = db.Column(db.Enum("cdi", "cdd", "stage", "consultant", "freelance", name="contract_type"), nullable=False)
    start_date = db.Column(db.Date, nullable=False, index=True)
    end_date = db.Column(db.Date, nullable=True, index=True)  # NULL pour CDI
    salary = db.Column(N18_2, nullable=True)  # Salaire mensuel
    currency = db.Column(db.String(8), nullable=False, default="GNF")
    position = db.Column(db.String(100), nullable=True)  # Poste dans ce contrat
    department = db.Column(db.String(100), nullable=True)  # Département dans ce contrat
    status = db.Column(db.Enum("draft", "active", "expired", "terminated", name="contract_status"), 
                       nullable=False, default="draft", index=True)
    termination_date = db.Column(db.Date, nullable=True)
    termination_reason = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    document_path = db.Column(db.String(500), nullable=True)  # Chemin vers le contrat signé
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(UTC))
    created_by_id = FK("users.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")
    
    created_by = db.relationship("User", foreign_keys=[created_by_id], backref="created_contracts")
    
    __table_args__ = (
        db.Index("idx_contract_employee", "employee_id"),
        db.Index("idx_contract_status", "status"),
        db.Index("idx_contract_dates", "start_date", "end_date"),
    )
    
    @property
    def is_active(self):
        """Vérifie si le contrat est actif"""
        today = date.today()
        if self.status != 'active':
            return False
        if self.start_date > today:
            return False
        if self.end_date and self.end_date < today:
            return False
        return True
    
    def __repr__(self):
        return f"<EmployeeContract {self.contract_number} - {self.contract_type}>"

class EmployeeTraining(db.Model):
    """Formations suivies par les employés"""
    __tablename__ = "employee_trainings"
    id = PK()
    employee_id = FK("employees.id", nullable=False, onupdate="CASCADE", ondelete="CASCADE", index=True)
    training_name = db.Column(db.String(200), nullable=False)
    training_type = db.Column(db.Enum("internal", "external", "online", "certification", name="training_type"), nullable=False)
    provider = db.Column(db.String(200), nullable=True)  # Organisme de formation
    start_date = db.Column(db.Date, nullable=False, index=True)
    end_date = db.Column(db.Date, nullable=True, index=True)
    duration_hours = db.Column(db.Integer, nullable=True)  # Durée en heures
    status = db.Column(db.Enum("planned", "in_progress", "completed", "cancelled", name="training_status"), 
                       nullable=False, default="planned", index=True)
    cost = db.Column(N18_2, nullable=True)  # Coût de la formation
    currency = db.Column(db.String(8), nullable=False, default="GNF")
    certificate_obtained = db.Column(db.Boolean, nullable=False, default=False)
    certificate_path = db.Column(db.String(500), nullable=True)  # Chemin vers le certificat
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(UTC))
    created_by_id = FK("users.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")
    
    created_by = db.relationship("User", foreign_keys=[created_by_id], backref="created_trainings")
    
    __table_args__ = (
        db.Index("idx_training_employee", "employee_id"),
        db.Index("idx_training_status", "status"),
        db.Index("idx_training_dates", "start_date", "end_date"),
    )
    
    def __repr__(self):
        return f"<EmployeeTraining {self.training_name} - {self.employee_id}>"

class EmployeeEvaluation(db.Model):
    """Évaluations de performance des employés"""
    __tablename__ = "employee_evaluations"
    id = PK()
    employee_id = FK("employees.id", nullable=False, onupdate="CASCADE", ondelete="CASCADE", index=True)
    evaluation_type = db.Column(db.Enum("annual", "probation", "mid_year", "project", "custom", name="evaluation_type"), nullable=False)
    evaluation_date = db.Column(db.Date, nullable=False, index=True)
    evaluator_id = FK("users.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")  # Évaluateur
    overall_rating = db.Column(db.Enum("excellent", "very_good", "good", "satisfactory", "needs_improvement", "unsatisfactory", name="rating"), nullable=True)
    overall_score = db.Column(N18_2, nullable=True)  # Score sur 100
    strengths = db.Column(db.Text, nullable=True)  # Points forts
    areas_for_improvement = db.Column(db.Text, nullable=True)  # Axes d'amélioration
    goals = db.Column(db.Text, nullable=True)  # Objectifs pour la prochaine période
    comments = db.Column(db.Text, nullable=True)  # Commentaires généraux
    status = db.Column(db.Enum("draft", "submitted", "reviewed", "approved", name="evaluation_status"), 
                       nullable=False, default="draft", index=True)
    document_path = db.Column(db.String(500), nullable=True)  # Chemin vers le document d'évaluation
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(UTC))
    created_by_id = FK("users.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")
    
    evaluator = db.relationship("User", foreign_keys=[evaluator_id], backref="conducted_evaluations")
    created_by = db.relationship("User", foreign_keys=[created_by_id], backref="created_evaluations")
    
    __table_args__ = (
        db.Index("idx_evaluation_employee", "employee_id"),
        db.Index("idx_evaluation_date", "evaluation_date"),
        db.Index("idx_evaluation_status", "status"),
    )
    
    def __repr__(self):
        return f"<EmployeeEvaluation {self.evaluation_type} - {self.employee_id} - {self.evaluation_date}>"

class EmployeeAbsence(db.Model):
    """Absences des employés (congés, maladie, etc.)"""
    __tablename__ = "employee_absences"
    id = PK()
    employee_id = FK("employees.id", nullable=False, onupdate="CASCADE", ondelete="CASCADE", index=True)
    absence_type = db.Column(db.Enum("vacation", "sick_leave", "personal", "maternity", "paternity", "unpaid", "other", name="absence_type"), nullable=False)
    start_date = db.Column(db.Date, nullable=False, index=True)
    end_date = db.Column(db.Date, nullable=False, index=True)
    days_count = db.Column(db.Integer, nullable=False)  # Nombre de jours
    status = db.Column(db.Enum("pending", "approved", "rejected", "cancelled", name="absence_status"), 
                       nullable=False, default="pending", index=True)
    reason = db.Column(db.Text, nullable=True)  # Raison de l'absence
    approved_by_id = FK("users.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")
    approved_at = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    medical_certificate_path = db.Column(db.String(500), nullable=True)  # Pour les arrêts maladie
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(UTC))
    created_by_id = FK("users.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")
    
    approved_by = db.relationship("User", foreign_keys=[approved_by_id], backref="approved_absences")
    created_by = db.relationship("User", foreign_keys=[created_by_id], backref="created_absences")
    
    __table_args__ = (
        db.Index("idx_absence_employee", "employee_id"),
        db.Index("idx_absence_dates", "start_date", "end_date"),
        db.Index("idx_absence_status", "status"),
        db.Index("idx_absence_type", "absence_type"),
    )
    
    @property
    def is_active(self):
        """Vérifie si l'absence est en cours"""
        today = date.today()
        return self.start_date <= today <= self.end_date and self.status == 'approved'
    
    def __repr__(self):
        return f"<EmployeeAbsence {self.absence_type} - {self.employee_id} - {self.start_date} to {self.end_date}>"

# =========================================================
# RÉFÉRENTIELS — RÉGIONS / DÉPÔTS / VÉHICULES / FAMILLES
# =========================================================

class Region(db.Model):
    __tablename__ = "regions"
    id = PK()
    name = db.Column(db.String(120), unique=True, nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(UTC))
    
    depots = db.relationship("Depot", backref="region", lazy="select")
    users = db.relationship("User", backref="region", lazy="select")
    
    __table_args__ = (
        db.Index("idx_region_name", "name"),
    )
    
    def __repr__(self):
        return f"<Region {self.name}>"

class Depot(db.Model):
    __tablename__ = "depots"
    id = PK()
    name = db.Column(db.String(120), unique=True, nullable=False)
    region_id = FK("regions.id", onupdate="CASCADE", ondelete="RESTRICT")
    address = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(UTC))
    
    stocks = db.relationship("DepotStock", backref="depot", lazy="select", cascade="all, delete-orphan")
    movements_from = db.relationship("StockMovement", foreign_keys="StockMovement.from_depot_id", backref="from_depot", lazy="dynamic")
    movements_to = db.relationship("StockMovement", foreign_keys="StockMovement.to_depot_id", backref="to_depot", lazy="dynamic")
    
    __table_args__ = (
        db.Index("idx_depot_name", "name"),
        db.Index("idx_depot_region", "region_id"),
    )
    
    def __repr__(self):
        return f"<Depot {self.name}>"

class Vehicle(db.Model):
    __tablename__ = "vehicles"
    id = PK()
    plate_number = db.Column(db.String(20), unique=True, nullable=False)
    brand = db.Column(db.String(50), nullable=True)
    model = db.Column(db.String(50), nullable=True)
    year = db.Column(db.Integer, nullable=True)
    color = db.Column(db.String(30), nullable=True)
    vin = db.Column(db.String(50), unique=True, nullable=True)
    whatsapp = db.Column(db.String(20), nullable=True)
    current_user_id = FK("users.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")
    acquisition_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.Enum("active", "inactive", "maintenance", name="vehicle_status"), nullable=False, default="active")
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(UTC))
    
    current_user = db.relationship("User", foreign_keys=[current_user_id], backref="assigned_vehicles")
    stocks = db.relationship("VehicleStock", backref="vehicle", lazy="select", cascade="all, delete-orphan")
    movements_from = db.relationship("StockMovement", foreign_keys="StockMovement.from_vehicle_id", backref="from_vehicle", lazy="dynamic")
    movements_to = db.relationship("StockMovement", foreign_keys="StockMovement.to_vehicle_id", backref="to_vehicle", lazy="dynamic")
    documents = db.relationship("VehicleDocument", backref="vehicle", lazy="select", cascade="all, delete-orphan")
    maintenances = db.relationship("VehicleMaintenance", backref="vehicle", lazy="select", cascade="all, delete-orphan")
    odometers = db.relationship("VehicleOdometer", backref="vehicle", lazy="select", cascade="all, delete-orphan", order_by="VehicleOdometer.reading_date.desc()")
    
    __table_args__ = (
        db.Index("idx_vehicle_plate", "plate_number"),
        db.Index("idx_vehicle_user", "current_user_id"),
        db.Index("idx_vehicle_status", "status"),
    )
    
    assignments = db.relationship("VehicleAssignment", backref="vehicle", lazy="select", cascade="all, delete-orphan", order_by="VehicleAssignment.start_date.desc()")
    
    def __repr__(self):
        return f"<Vehicle {self.plate_number}>"

class VehicleAssignment(db.Model):
    """Historique des assignations de conducteurs aux véhicules"""
    __tablename__ = "vehicle_assignments"
    id = PK()
    vehicle_id = FK("vehicles.id", onupdate="CASCADE", ondelete="CASCADE")
    user_id = FK("users.id", onupdate="CASCADE", ondelete="RESTRICT")
    start_date = db.Column(db.Date, nullable=False, index=True)
    end_date = db.Column(db.Date, nullable=True, index=True)
    reason = db.Column(db.String(255), nullable=True)  # Raison de l'assignation ou du changement
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    created_by_id = FK("users.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")  # Qui a créé l'assignation
    
    user = db.relationship("User", foreign_keys=[user_id], backref="vehicle_assignments", lazy="joined")
    created_by = db.relationship("User", foreign_keys=[created_by_id], lazy="joined")
    
    __table_args__ = (
        db.Index("idx_vehicleassignment_vehicle", "vehicle_id"),
        db.Index("idx_vehicleassignment_user", "user_id"),
        db.Index("idx_vehicleassignment_dates", "start_date", "end_date"),
    )
    
    @property
    def is_active(self):
        """Vérifie si l'assignation est active (pas de date de fin)"""
        return self.end_date is None
    
    @property
    def duration_days(self):
        """Calcule la durée de l'assignation en jours"""
        if not self.start_date:
            return None
        end = self.end_date if self.end_date else date.today()
        return (end - self.start_date).days
    
    def __repr__(self):
        return f"<VehicleAssignment vehicle={self.vehicle_id} user={self.user_id} {self.start_date} - {self.end_date or 'active'}>"

class Family(db.Model):
    __tablename__ = "families"
    id = PK()
    name = db.Column(db.String(120), unique=True, nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(UTC))
    
    stock_items = db.relationship("StockItem", backref="family", lazy="select")
    
    __table_args__ = (
        db.Index("idx_family_name", "name"),
    )
    
    def __repr__(self):
        return f"<Family {self.name}>"

class StockItem(db.Model):
    __tablename__ = "stock_items"
    id = PK()
    sku = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(160), nullable=False)
    family_id = FK("families.id", onupdate="CASCADE", ondelete="RESTRICT")
    purchase_price_gnf = db.Column(N18_2, nullable=False, default=Decimal("0.00"))
    unit_weight_kg = db.Column(N18_4, nullable=False, default=Decimal("0.0000"))
    description = db.Column(db.Text, nullable=True)
    min_stock_depot = db.Column(N18_4, nullable=False, default=Decimal("0.0000"))
    min_stock_vehicle = db.Column(N18_4, nullable=False, default=Decimal("0.0000"))
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(UTC))
    
    depot_stocks = db.relationship("DepotStock", backref="stock_item", lazy="select", cascade="all, delete-orphan")
    vehicle_stocks = db.relationship("VehicleStock", backref="stock_item", lazy="select", cascade="all, delete-orphan")
    movements = db.relationship("StockMovement", backref="stock_item", lazy="dynamic")
    
    __table_args__ = (
        db.Index("idx_stockitem_sku", "sku"),
        db.Index("idx_stockitem_name", "name"),
        db.Index("idx_stockitem_family", "family_id"),
    )
    
    def __repr__(self):
        return f"<StockItem {self.sku} - {self.name}>"

# =========================================================
# STOCKS — DÉPÔT / VÉHICULE
# =========================================================

class DepotStock(db.Model):
    __tablename__ = "depot_stocks"
    id = PK()
    depot_id = FK("depots.id", onupdate="CASCADE", ondelete="CASCADE")
    stock_item_id = FK("stock_items.id", onupdate="CASCADE", ondelete="CASCADE")
    quantity = db.Column(N18_4, nullable=False, default=Decimal("0.0000"))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    __table_args__ = (
        db.UniqueConstraint("depot_id", "stock_item_id", name="uq_depot_stock"),
        db.Index("idx_depotstock_depot", "depot_id"),
        db.Index("idx_depotstock_item", "stock_item_id"),
    )
    
    def __repr__(self):
        return f"<DepotStock depot={self.depot_id} item={self.stock_item_id} qty={self.quantity}>"

class VehicleStock(db.Model):
    __tablename__ = "vehicle_stocks"
    id = PK()
    vehicle_id = FK("vehicles.id", onupdate="CASCADE", ondelete="CASCADE")
    stock_item_id = FK("stock_items.id", onupdate="CASCADE", ondelete="CASCADE")
    quantity = db.Column(N18_4, nullable=False, default=Decimal("0.0000"))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    __table_args__ = (
        db.UniqueConstraint("vehicle_id", "stock_item_id", name="uq_vehicle_stock"),
        db.Index("idx_vehiclestock_vehicle", "vehicle_id"),
        db.Index("idx_vehiclestock_item", "stock_item_id"),
    )
    
    def __repr__(self):
        return f"<VehicleStock vehicle={self.vehicle_id} item={self.stock_item_id} qty={self.quantity}>"

class StockMovement(db.Model):
    __tablename__ = "stock_movements"
    id = PK()
    reference = db.Column(db.String(50), nullable=True, unique=True, index=True)
    movement_type = db.Column(db.Enum("transfer", "reception", "reception_return", "adjustment", "inventory", name="movement_type"), nullable=False)
    movement_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC), index=True)
    stock_item_id = FK("stock_items.id", onupdate="CASCADE", ondelete="RESTRICT")
    quantity = db.Column(N18_4, nullable=False)
    user_id = FK("users.id", onupdate="CASCADE", ondelete="SET NULL")
    
    # Source (from)
    from_depot_id = FK("depots.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")
    from_vehicle_id = FK("vehicles.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")
    
    # Destination (to)
    to_depot_id = FK("depots.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")
    to_vehicle_id = FK("vehicles.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")
    
    # Réception
    supplier_name = db.Column(db.String(120), nullable=True)
    bl_number = db.Column(db.String(50), nullable=True)
    
    # Ajustement/Inventaire
    reason = db.Column(db.Text, nullable=True)
    inventory_session_id = FK("inventory_sessions.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")
    
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    
    inventory_session = db.relationship("InventorySession", backref="movements", lazy="select")
    
    __table_args__ = (
        db.Index("idx_movement_date", "movement_date"),
        db.Index("idx_movement_type", "movement_type"),
        db.Index("idx_movement_item", "stock_item_id"),
        db.Index("idx_movement_user", "user_id"),
    )
    
    def __repr__(self):
        return f"<StockMovement {self.movement_type} item={self.stock_item_id} qty={self.quantity}>"

class Reception(db.Model):
    __tablename__ = "receptions"
    id = PK()
    reference = db.Column(db.String(50), unique=True, nullable=False, index=True)  # Référence unique
    reception_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC), index=True)
    depot_id = FK("depots.id", onupdate="CASCADE", ondelete="RESTRICT")
    supplier_name = db.Column(db.String(120), nullable=False)
    bl_number = db.Column(db.String(50), nullable=False)
    user_id = FK("users.id", onupdate="CASCADE", ondelete="SET NULL")
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.Enum("draft", "completed", "cancelled", name="reception_status"), nullable=False, default="draft")
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(UTC))
    
    user = db.relationship("User", foreign_keys=[user_id], lazy="joined")
    depot = db.relationship("Depot", lazy="joined")
    details = db.relationship("ReceptionDetail", backref="reception", lazy="select", cascade="all, delete-orphan")
    
    __table_args__ = (
        db.Index("idx_reception_date", "reception_date"),
        db.Index("idx_reception_depot", "depot_id"),
        db.Index("idx_reception_reference", "reference"),
    )
    
    def __repr__(self):
        return f"<Reception {self.reference} at {self.depot_id}>"

class ReceptionDetail(db.Model):
    __tablename__ = "reception_details"
    id = PK()
    reception_id = FK("receptions.id", onupdate="CASCADE", ondelete="CASCADE")
    stock_item_id = FK("stock_items.id", onupdate="CASCADE", ondelete="RESTRICT")
    quantity = db.Column(N18_4, nullable=False)
    unit_price_gnf = db.Column(N18_2, nullable=True)  # Prix unitaire à la réception
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    
    stock_item = db.relationship("StockItem", lazy="joined")
    
    __table_args__ = (
        db.UniqueConstraint("reception_id", "stock_item_id", name="uq_reception_detail"),
        db.Index("idx_receptiondetail_reception", "reception_id"),
        db.Index("idx_receptiondetail_item", "stock_item_id"),
    )
    
    def __repr__(self):
        return f"<ReceptionDetail reception={self.reception_id} item={self.stock_item_id} qty={self.quantity}>"

class StockOutgoing(db.Model):
    """Sorties de stock (ventes aux clients)"""
    __tablename__ = "stock_outgoings"
    id = PK()
    reference = db.Column(db.String(50), unique=True, nullable=False, index=True)  # Référence unique
    outgoing_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC), index=True)
    client_name = db.Column(db.String(120), nullable=False)
    client_phone = db.Column(db.String(20), nullable=True)
    commercial_id = FK("users.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")  # Commercial responsable
    vehicle_id = FK("vehicles.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")  # Véhicule utilisé
    depot_id = FK("depots.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")  # Dépôt source
    user_id = FK("users.id", onupdate="CASCADE", ondelete="SET NULL")  # Utilisateur qui a créé
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.Enum("draft", "completed", "cancelled", name="outgoing_status"), nullable=False, default="draft")
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(UTC))
    
    commercial = db.relationship("User", foreign_keys=[commercial_id], lazy="joined")
    user = db.relationship("User", foreign_keys=[user_id], lazy="joined")
    vehicle = db.relationship("Vehicle", lazy="joined")
    depot = db.relationship("Depot", lazy="joined")
    details = db.relationship("StockOutgoingDetail", backref="outgoing", lazy="select", cascade="all, delete-orphan")
    
    __table_args__ = (
        db.Index("idx_outgoing_date", "outgoing_date"),
        db.Index("idx_outgoing_reference", "reference"),
        db.Index("idx_outgoing_commercial", "commercial_id"),
    )
    
    def __repr__(self):
        return f"<StockOutgoing {self.reference} to {self.client_name}>"

class StockOutgoingDetail(db.Model):
    __tablename__ = "stock_outgoing_details"
    id = PK()
    outgoing_id = FK("stock_outgoings.id", onupdate="CASCADE", ondelete="CASCADE")
    stock_item_id = FK("stock_items.id", onupdate="CASCADE", ondelete="RESTRICT")
    quantity = db.Column(N18_4, nullable=False)
    unit_price_gnf = db.Column(N18_2, nullable=True)  # Prix de vente unitaire
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    
    stock_item = db.relationship("StockItem", lazy="joined")
    
    __table_args__ = (
        db.UniqueConstraint("outgoing_id", "stock_item_id", name="uq_outgoing_detail"),
        db.Index("idx_outgoingdetail_outgoing", "outgoing_id"),
        db.Index("idx_outgoingdetail_item", "stock_item_id"),
    )
    
    def __repr__(self):
        return f"<StockOutgoingDetail outgoing={self.outgoing_id} item={self.stock_item_id} qty={self.quantity}>"

class StockReturn(db.Model):
    """Retours de stock (retours clients ou retours fournisseurs)"""
    __tablename__ = "stock_returns"
    id = PK()
    reference = db.Column(db.String(50), unique=True, nullable=False, index=True)  # Référence unique
    return_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC), index=True)
    
    # Type de retour : 'client' (retour client) ou 'supplier' (retour fournisseur = mouvement inverse de réception)
    return_type = db.Column(db.Enum("client", "supplier", name="return_type"), nullable=False, default="client", index=True)
    
    # Champs pour retours clients
    client_name = db.Column(db.String(120), nullable=True)  # Modifié en nullable pour permettre retours fournisseurs
    client_phone = db.Column(db.String(20), nullable=True)
    original_outgoing_id = FK("stock_outgoings.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")  # Référence sortie originale
    original_order_id = FK("commercial_orders.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")  # Référence commande originale (optionnel)
    
    # Champs pour retours fournisseurs (mouvement inverse de réception)
    supplier_name = db.Column(db.String(120), nullable=True)  # Nom du fournisseur pour retours fournisseurs
    original_reception_id = FK("receptions.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")  # Référence réception originale
    
    commercial_id = FK("users.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")
    vehicle_id = FK("vehicles.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")
    depot_id = FK("depots.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")
    user_id = FK("users.id", onupdate="CASCADE", ondelete="SET NULL")
    reason = db.Column(db.Text, nullable=True)  # Raison du retour
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.Enum("draft", "completed", "cancelled", name="return_status"), nullable=False, default="draft")
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(UTC))
    
    original_outgoing = db.relationship("StockOutgoing", foreign_keys=[original_outgoing_id], lazy="joined")
    original_order = db.relationship("CommercialOrder", foreign_keys=[original_order_id], lazy="joined")
    original_reception = db.relationship("Reception", foreign_keys=[original_reception_id], lazy="joined")
    commercial = db.relationship("User", foreign_keys=[commercial_id], lazy="joined")
    user = db.relationship("User", foreign_keys=[user_id], lazy="joined")
    vehicle = db.relationship("Vehicle", lazy="joined")
    depot = db.relationship("Depot", lazy="joined")
    details = db.relationship("StockReturnDetail", backref="stock_return", lazy="select", cascade="all, delete-orphan")
    
    __table_args__ = (
        db.Index("idx_return_date", "return_date"),
        db.Index("idx_return_reference", "reference"),
        db.Index("idx_return_type", "return_type"),
        db.Index("idx_return_outgoing", "original_outgoing_id"),
        db.Index("idx_return_order", "original_order_id"),
        db.Index("idx_return_reception", "original_reception_id"),
    )
    
    def __repr__(self):
        if self.return_type == 'supplier':
            return f"<StockReturn {self.reference} to {self.supplier_name}>"
        return f"<StockReturn {self.reference} from {self.client_name}>"

class StockReturnDetail(db.Model):
    __tablename__ = "stock_return_details"
    id = PK()
    return_id = FK("stock_returns.id", onupdate="CASCADE", ondelete="CASCADE")
    stock_item_id = FK("stock_items.id", onupdate="CASCADE", ondelete="RESTRICT")
    quantity = db.Column(N18_4, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    
    stock_item = db.relationship("StockItem", lazy="joined")
    
    __table_args__ = (
        db.UniqueConstraint("return_id", "stock_item_id", name="uq_return_detail"),
        db.Index("idx_returndetail_return", "return_id"),
        db.Index("idx_returndetail_item", "stock_item_id"),
    )
    
    def __repr__(self):
        return f"<StockReturnDetail return={self.return_id} item={self.stock_item_id} qty={self.quantity}>"

# =========================================================
# COMMANDES COMMERCIALES
# =========================================================

class CommercialOrder(db.Model):
    """Commandes commerciales avec validation hiérarchique"""
    __tablename__ = "commercial_orders"
    id = PK()
    reference = db.Column(db.String(50), unique=True, nullable=False, index=True)  # Référence unique
    order_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC), index=True)
    commercial_id = FK("users.id", nullable=False, onupdate="CASCADE", ondelete="RESTRICT")  # Commercial qui crée la commande
    region_id = FK("regions.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")  # Région du commercial
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.Enum("draft", "pending_validation", "validated", "rejected", "completed", name="order_status"), 
                      nullable=False, default="draft", index=True)
    validated_by_id = FK("users.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")  # Hiérarchie qui valide
    validated_at = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)  # Raison du rejet
    user_id = FK("users.id", onupdate="CASCADE", ondelete="SET NULL")  # Utilisateur qui a créé
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(UTC))
    
    commercial = db.relationship("User", foreign_keys=[commercial_id], lazy="joined")
    validator = db.relationship("User", foreign_keys=[validated_by_id], lazy="joined")
    user = db.relationship("User", foreign_keys=[user_id], lazy="joined")
    region = db.relationship("Region", lazy="joined")
    clients = db.relationship("CommercialOrderClient", backref="order", lazy="select", cascade="all, delete-orphan", order_by="CommercialOrderClient.id")
    
    __table_args__ = (
        db.Index("idx_order_date", "order_date"),
        db.Index("idx_order_reference", "reference"),
        db.Index("idx_order_commercial", "commercial_id"),
        db.Index("idx_order_status", "status"),
    )
    
    def __repr__(self):
        return f"<CommercialOrder {self.reference} by {self.commercial_id} status={self.status}>"

class CommercialOrderClient(db.Model):
    """Clients dans une commande commerciale"""
    __tablename__ = "commercial_order_clients"
    id = PK()
    order_id = FK("commercial_orders.id", nullable=False, onupdate="CASCADE", ondelete="CASCADE")
    client_name = db.Column(db.String(120), nullable=False)
    client_phone = db.Column(db.String(20), nullable=True)
    client_address = db.Column(db.String(255), nullable=True)
    payment_type = db.Column(db.Enum("cash", "credit", name="payment_type"), nullable=False, default="cash")  # Type de paiement
    payment_due_date = db.Column(db.Date, nullable=True)  # Échéance de paiement (si crédit)
    notes = db.Column(db.Text, nullable=True)  # Observations générales
    comments = db.Column(db.Text, nullable=True)  # Commentaires spécifiques (échéance, conditions, etc.)
    status = db.Column(db.Enum("pending", "approved", "rejected", name="client_status"), nullable=False, default="pending", index=True)  # Statut du client dans la commande
    rejection_reason = db.Column(db.Text, nullable=True)  # Raison du rejet du client
    rejected_by_id = FK("users.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")  # Utilisateur qui a rejeté le client
    rejected_at = db.Column(db.DateTime, nullable=True)  # Date de rejet
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    
    items = db.relationship("CommercialOrderItem", backref="order_client", lazy="select", cascade="all, delete-orphan", order_by="CommercialOrderItem.id")
    rejected_by = db.relationship("User", foreign_keys=[rejected_by_id], lazy="joined")
    
    __table_args__ = (
        db.Index("idx_orderclient_order", "order_id"),
        db.Index("idx_orderclient_status", "status"),
    )
    
    def __repr__(self):
        return f"<CommercialOrderClient order={self.order_id} client={self.client_name} status={self.status}>"

class CommercialOrderItem(db.Model):
    """Articles commandés pour un client"""
    __tablename__ = "commercial_order_items"
    id = PK()
    order_client_id = FK("commercial_order_clients.id", nullable=False, onupdate="CASCADE", ondelete="CASCADE")
    stock_item_id = FK("stock_items.id", nullable=False, onupdate="CASCADE", ondelete="RESTRICT")
    quantity = db.Column(N18_4, nullable=False)
    unit_price_gnf = db.Column(N18_2, nullable=True)  # Prix unitaire de vente prévu
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    
    stock_item = db.relationship("StockItem", lazy="joined")
    
    __table_args__ = (
        db.Index("idx_orderitem_client", "order_client_id"),
        db.Index("idx_orderitem_item", "stock_item_id"),
    )
    
    def __repr__(self):
        return f"<CommercialOrderItem client={self.order_client_id} item={self.stock_item_id} qty={self.quantity}>"

# =========================================================
# RÉCAPITULATIFS DE CHARGEMENT DE STOCK
# =========================================================

class StockLoadingSummary(db.Model):
    """Récapitulatif de chargement de stock pour une commande validée"""
    __tablename__ = "stock_loading_summaries"
    id = PK()
    order_id = FK("commercial_orders.id", nullable=False, unique=True, onupdate="CASCADE", ondelete="CASCADE")
    commercial_id = FK("users.id", nullable=False, onupdate="CASCADE", ondelete="RESTRICT")
    commercial_depot_id = FK("depots.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")
    commercial_vehicle_id = FK("vehicles.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")
    source_depot_id = FK("depots.id", nullable=False, onupdate="CASCADE", ondelete="RESTRICT")
    status = db.Column(db.Enum("pending", "stock_checked", "loading_in_progress", "completed", "cancelled", name="loading_status"), 
                       nullable=False, default="pending", index=True)
    pre_loading_stock_verified = db.Column(db.Boolean, nullable=False, default=False)
    pre_loading_stock_verified_at = db.Column(db.DateTime, nullable=True)
    pre_loading_stock_verified_by_id = FK("users.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")
    post_loading_stock_verified = db.Column(db.Boolean, nullable=False, default=False)
    post_loading_stock_verified_at = db.Column(db.DateTime, nullable=True)
    post_loading_stock_verified_by_id = FK("users.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")
    loading_completed_at = db.Column(db.DateTime, nullable=True)
    loading_completed_by_id = FK("users.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(UTC))
    
    order = db.relationship("CommercialOrder", backref="loading_summary", lazy="joined")
    commercial = db.relationship("User", foreign_keys=[commercial_id], lazy="joined")
    commercial_depot = db.relationship("Depot", foreign_keys=[commercial_depot_id], lazy="joined")
    commercial_vehicle = db.relationship("Vehicle", lazy="joined")
    source_depot = db.relationship("Depot", foreign_keys=[source_depot_id], lazy="joined")
    pre_verifier = db.relationship("User", foreign_keys=[pre_loading_stock_verified_by_id], lazy="joined")
    post_verifier = db.relationship("User", foreign_keys=[post_loading_stock_verified_by_id], lazy="joined")
    loader = db.relationship("User", foreign_keys=[loading_completed_by_id], lazy="joined")
    items = db.relationship("StockLoadingSummaryItem", backref="summary", lazy="select", cascade="all, delete-orphan")
    
    __table_args__ = (
        db.Index("idx_loadingsummary_order", "order_id"),
        db.Index("idx_loadingsummary_commercial", "commercial_id"),
        db.Index("idx_loadingsummary_status", "status"),
    )
    
    def __repr__(self):
        return f"<StockLoadingSummary order={self.order_id} commercial={self.commercial_id} status={self.status}>"

class StockLoadingSummaryItem(db.Model):
    """Articles dans un récapitulatif de chargement"""
    __tablename__ = "stock_loading_summary_items"
    id = PK()
    summary_id = FK("stock_loading_summaries.id", nullable=False, onupdate="CASCADE", ondelete="CASCADE")
    stock_item_id = FK("stock_items.id", nullable=False, onupdate="CASCADE", ondelete="RESTRICT")
    quantity_required = db.Column(N18_4, nullable=False)  # Quantité requise depuis la commande
    quantity_loaded = db.Column(N18_4, nullable=False, default=Decimal("0.0000"))  # Quantité effectivement chargée
    pre_loading_stock_remaining = db.Column(N18_4, nullable=True)  # Stock restant avant chargement (si > 0)
    post_loading_stock_remaining = db.Column(N18_4, nullable=True)  # Stock restant après chargement (si > 0)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    
    stock_item = db.relationship("StockItem", lazy="joined")
    
    __table_args__ = (
        db.Index("idx_loadingsummaryitem_summary", "summary_id"),
        db.Index("idx_loadingsummaryitem_item", "stock_item_id"),
    )
    
    def __repr__(self):
        return f"<StockLoadingSummaryItem summary={self.summary_id} item={self.stock_item_id} qty_required={self.quantity_required}>"

# =========================================================
# INVENTAIRES
# =========================================================

class InventorySession(db.Model):
    __tablename__ = "inventory_sessions"
    id = PK()
    session_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC), index=True)
    depot_id = FK("depots.id", onupdate="CASCADE", ondelete="RESTRICT")
    operator_id = FK("users.id", onupdate="CASCADE", ondelete="SET NULL")
    status = db.Column(db.Enum("draft", "in_progress", "completed", "validated", name="inventory_status"), nullable=False, default="draft")
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(UTC))
    validated_at = db.Column(db.DateTime, nullable=True)
    validated_by_id = FK("users.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")
    
    depot = db.relationship("Depot", lazy="joined")
    operator = db.relationship("User", foreign_keys=[operator_id], backref="inventory_sessions_operated", lazy="joined")
    validator = db.relationship("User", foreign_keys=[validated_by_id], backref="inventory_sessions_validated", lazy="joined")
    details = db.relationship("InventoryDetail", backref="session", lazy="select", cascade="all, delete-orphan")
    
    __table_args__ = (
        db.Index("idx_inventory_date", "session_date"),
        db.Index("idx_inventory_depot", "depot_id"),
        db.Index("idx_inventory_status", "status"),
    )
    
    def __repr__(self):
        return f"<InventorySession {self.id} depot={self.depot_id} status={self.status}>"

class InventoryDetail(db.Model):
    __tablename__ = "inventory_details"
    id = PK()
    session_id = FK("inventory_sessions.id", onupdate="CASCADE", ondelete="CASCADE")
    stock_item_id = FK("stock_items.id", onupdate="CASCADE", ondelete="RESTRICT")
    system_quantity = db.Column(N18_4, nullable=False)  # Quantité système
    counted_quantity = db.Column(N18_4, nullable=False)  # Quantité comptée (inclut la pile si calculée)
    pile_dimensions = db.Column(db.String(100), nullable=True)  # Ex: "2x5+3x4"
    variance = db.Column(N18_4, nullable=False)  # system - counted (stock actuel - quantité comptée)
    reason = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    
    stock_item = db.relationship("StockItem", lazy="joined")
    
    __table_args__ = (
        db.UniqueConstraint("session_id", "stock_item_id", name="uq_inventory_detail"),
        db.Index("idx_inventorydetail_session", "session_id"),
        db.Index("idx_inventorydetail_item", "stock_item_id"),
    )
    
    def __repr__(self):
        return f"<InventoryDetail session={self.session_id} item={self.stock_item_id} var={self.variance}>"

# =========================================================
# FLOTTE — DOCUMENTS / MAINTENANCE / ODOMÈTRE
# =========================================================

class VehicleDocument(db.Model):
    __tablename__ = "vehicle_documents"
    id = PK()
    vehicle_id = FK("vehicles.id", onupdate="CASCADE", ondelete="CASCADE")
    document_type = db.Column(db.Enum("insurance", "registration", "technical_inspection", "road_tax", "license", "other", name="doc_type"), nullable=False)
    document_number = db.Column(db.String(100), nullable=True)
    issue_date = db.Column(db.Date, nullable=True)
    expiry_date = db.Column(db.Date, nullable=False, index=True)
    attachment_url = db.Column(db.String(500), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(UTC))
    
    __table_args__ = (
        db.Index("idx_vehicledoc_vehicle", "vehicle_id"),
        db.Index("idx_vehicledoc_type", "document_type"),
        db.Index("idx_vehicledoc_expiry", "expiry_date"),
    )
    
    @property
    def status(self):
        """Calculer le statut du document (valid/expiring/expired)"""
        if not self.expiry_date:
            return "unknown"
        today = date.today()
        days_until_expiry = (self.expiry_date - today).days
        if days_until_expiry < 0:
            return "expired"
        elif days_until_expiry <= 7:
            return "expiring"
        else:
            return "valid"
    
    def __repr__(self):
        return f"<VehicleDocument {self.document_type} vehicle={self.vehicle_id} expires={self.expiry_date}>"

class VehicleMaintenance(db.Model):
    __tablename__ = "vehicle_maintenances"
    id = PK()
    vehicle_id = FK("vehicles.id", onupdate="CASCADE", ondelete="CASCADE")
    maintenance_type = db.Column(db.String(50), nullable=False)  # vidange, pneus, freins, etc.
    status = db.Column(db.Enum("planned", "completed", "cancelled", name="maintenance_status"), nullable=False, default="planned")
    planned_date = db.Column(db.Date, nullable=True, index=True)
    completed_date = db.Column(db.Date, nullable=True)
    due_at_km = db.Column(db.Integer, nullable=True, index=True)
    cost_gnf = db.Column(N18_2, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(UTC))
    
    __table_args__ = (
        db.Index("idx_vehiclemaint_vehicle", "vehicle_id"),
        db.Index("idx_vehiclemaint_status", "status"),
        db.Index("idx_vehiclemaint_planned", "planned_date"),
    )
    
    def __repr__(self):
        return f"<VehicleMaintenance {self.maintenance_type} vehicle={self.vehicle_id} status={self.status}>"

class VehicleOdometer(db.Model):
    __tablename__ = "vehicle_odometers"
    id = PK()
    vehicle_id = FK("vehicles.id", onupdate="CASCADE", ondelete="CASCADE")
    reading_date = db.Column(db.Date, nullable=False, index=True)
    odometer_km = db.Column(db.Integer, nullable=False)
    source = db.Column(db.Enum("manual", "gps", "system", name="odometer_source"), nullable=False, default="manual")
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    
    __table_args__ = (
        db.Index("idx_vehicleodo_vehicle", "vehicle_id"),
        db.Index("idx_vehicleodo_date", "reading_date"),
    )
    
    def __repr__(self):
        return f"<VehicleOdometer vehicle={self.vehicle_id} km={self.odometer_km} date={self.reading_date}>"

# =========================================================
# FICHES DE PRIX — PRIX GROSSISTE / DÉTAILLANT / GRATUITÉS
# =========================================================

class PriceList(db.Model):
    """Fiche de prix avec période de validité"""
    __tablename__ = "price_lists"
    id = PK()
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    start_date = db.Column(db.Date, nullable=False, index=True)
    end_date = db.Column(db.Date, nullable=True, index=True)  # NULL = pas de fin
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_by_id = FK("users.id", nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(UTC))
    
    created_by = db.relationship("User", backref=db.backref("price_lists", lazy="select"))
    items = db.relationship("PriceListItem", backref="price_list",
                            cascade="all, delete-orphan", lazy="selectin",
                            order_by="PriceListItem.stock_item_id")
    
    __table_args__ = (
        db.Index("idx_pricelist_dates", "start_date", "end_date"),
        db.Index("idx_pricelist_active", "is_active"),
    )
    
    @property
    def status(self):
        """Statut de la fiche de prix (active, upcoming, expired)"""
        today = date.today()
        if not self.is_active:
            return "inactive"
        if self.start_date > today:
            return "upcoming"
        if self.end_date and self.end_date < today:
            return "expired"
        return "active"
    
    def __repr__(self):
        return f"<PriceList {self.name} ({self.start_date} - {self.end_date or '∞'})>"

class PriceListItem(db.Model):
    """Prix d'un article de stock dans une fiche de prix"""
    __tablename__ = "price_list_items"
    id = PK()
    price_list_id = FK("price_lists.id", onupdate="CASCADE", ondelete="CASCADE")
    stock_item_id = FK("stock_items.id", onupdate="CASCADE", ondelete="CASCADE")
    
    # Prix en GNF
    wholesale_price = db.Column(N18_2, nullable=True)  # Prix grossiste
    retail_price = db.Column(N18_2, nullable=True)     # Prix détaillant
    
    # Gratuités au format: "25+1,50+2,100+5" (quantité+nombre_gratuit)
    freebies = db.Column(db.String(200), nullable=True)
    
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(UTC))
    
    stock_item = db.relationship("StockItem", backref=db.backref("price_list_items", lazy="select"))
    
    __table_args__ = (
        db.UniqueConstraint("price_list_id", "stock_item_id", name="uk_pricelistitem_unique"),
        db.Index("idx_pricelistitem_stock_item", "stock_item_id"),
    )
    
    def parse_freebies(self):
        """Parser les gratuités en liste de dicts"""
        if not self.freebies:
            return []
        result = []
        for item in self.freebies.split(','):
            item = item.strip()
            if '+' in item:
                try:
                    parts = item.split('+')
                    quantity = int(parts[0].strip())
                    free = int(parts[1].strip())
                    result.append({'quantity': quantity, 'free': free})
                except (ValueError, IndexError):
                    continue
        return sorted(result, key=lambda x: x['quantity'])
    
    def format_freebies(self):
        """Formater les gratuités pour affichage"""
        freebies = self.parse_freebies()
        if not freebies:
            return "-"
        return ", ".join([f"{f['quantity']}+{f['free']}" for f in freebies])
    
    def __repr__(self):
        return f"<PriceListItem price_list={self.price_list_id} stock_item={self.stock_item_id}>"

# =========================================================
# PRÉVISIONS & VENTES — FORECAST
# =========================================================

class Forecast(db.Model):
    """Prévision de ventes"""
    __tablename__ = "forecasts"
    id = PK()
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    start_date = db.Column(db.Date, nullable=False, index=True)
    end_date = db.Column(db.Date, nullable=False, index=True)
    status = db.Column(db.Enum("draft", "active", "completed", "archived", name="forecast_status"), 
                      nullable=False, default="draft")
    commercial_name = db.Column(db.String(100), nullable=True, index=True)  # Nom du commercial/vendeur
    currency = db.Column(db.String(8), nullable=False, default="GNF")  # Devise principale (USD, EUR, XOF, GNF)
    rate_usd = db.Column(N18_2, nullable=True)  # Taux USD au moment de la création
    rate_eur = db.Column(N18_2, nullable=True)  # Taux EUR au moment de la création
    rate_xof = db.Column(N18_2, nullable=True)  # Taux XOF au moment de la création
    total_forecast_value = db.Column(N18_2, nullable=False, default=Decimal("0.00"))  # En devise principale
    total_realized_value = db.Column(N18_2, nullable=False, default=Decimal("0.00"))  # En devise principale
    created_by_id = FK("users.id", nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(UTC))
    
    created_by = db.relationship("User", backref=db.backref("forecasts", lazy="select"))
    items = db.relationship("ForecastItem", backref="forecast",
                           cascade="all, delete-orphan", lazy="selectin",
                           order_by="ForecastItem.id")
    
    __table_args__ = (
        db.Index("idx_forecast_dates", "start_date", "end_date"),
        db.Index("idx_forecast_status", "status"),
    )
    
    @property
    def realization_percentage(self):
        """Pourcentage de réalisation global"""
        if self.total_forecast_value and self.total_forecast_value > 0:
            return (float(self.total_realized_value) / float(self.total_forecast_value)) * 100
        return 0.0
    
    def __repr__(self):
        return f"<Forecast {self.name} ({self.start_date} - {self.end_date})>"

class ForecastItem(db.Model):
    """Article dans une prévision"""
    __tablename__ = "forecast_items"
    id = PK()
    forecast_id = FK("forecasts.id", onupdate="CASCADE", ondelete="CASCADE")
    stock_item_id = FK("stock_items.id", onupdate="CASCADE", ondelete="RESTRICT")
    
    # Prévisions
    forecast_quantity = db.Column(N18_4, nullable=False, default=Decimal("0.0000"))
    selling_price_gnf = db.Column(N18_2, nullable=False, default=Decimal("0.00"))  # Prix de vente en gros
    
    # Réalisations (calculées depuis StockOutgoing)
    realized_quantity = db.Column(N18_4, nullable=False, default=Decimal("0.0000"))  # Moyenne réalisée
    realized_value_gnf = db.Column(N18_2, nullable=False, default=Decimal("0.00"))  # Valeur réalisée
    
    # Métriques calculées
    realization_percentage = db.Column(N18_2, nullable=False, default=Decimal("0.00"))  # Real%
    equivalent_quantity = db.Column(N18_4, nullable=False, default=Decimal("0.0000"))  # EQ
    evaluated_value = db.Column(N18_2, nullable=False, default=Decimal("0.00"))  # EVal
    evaluated_value_cfa = db.Column(N18_2, nullable=False, default=Decimal("0.00"))  # EVALCFA
    deviation_50pct = db.Column(N18_4, nullable=False, default=Decimal("0.0000"))  # ECART A 50%
    quantity_available = db.Column(N18_4, nullable=False, default=Decimal("0.0000"))  # QAF
    number_of_days = db.Column(db.Integer, nullable=False, default=1)  # Nb Jr
    
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(UTC))
    
    stock_item = db.relationship("StockItem", lazy="joined")
    
    __table_args__ = (
        db.UniqueConstraint("forecast_id", "stock_item_id", name="uq_forecast_item"),
        db.Index("idx_forecastitem_forecast", "forecast_id"),
        db.Index("idx_forecastitem_item", "stock_item_id"),
    )
    
    @property
    def forecast_value(self):
        """Valeur prévisionnelle (PRIX × FORCAST)"""
        return float(self.selling_price_gnf) * float(self.forecast_quantity)
    
    def __repr__(self):
        return f"<ForecastItem forecast={self.forecast_id} item={self.stock_item_id} qty={self.forecast_quantity}>"

# =========================================================
# CHAT INTERNE — MESSAGERIE INTERNE AVEC PIÈCES JOINTES
# =========================================================

class ChatRoom(db.Model):
    """Conversation (direct, groupe ou canal)"""
    __tablename__ = "chat_rooms"
    id = PK()
    name = db.Column(db.String(200), nullable=True)  # NULL pour conversations 1-1, nom pour groupes
    room_type = db.Column(db.Enum("direct", "group", "channel", name="room_type"), nullable=False, default="direct")
    created_by_id = FK("users.id", nullable=False, ondelete="RESTRICT", onupdate="CASCADE")
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(UTC))
    
    created_by = db.relationship("User", backref=db.backref("created_chat_rooms", lazy="select"))
    members = db.relationship("ChatRoomMember", backref="room", cascade="all, delete-orphan", lazy="selectin")
    messages = db.relationship("ChatMessage", backref="room", cascade="all, delete-orphan", lazy="dynamic", order_by="ChatMessage.created_at")
    
    __table_args__ = (
        db.Index("idx_chatroom_creator", "created_by_id"),
        db.Index("idx_chatroom_type", "room_type"),
    )
    
    def __repr__(self):
        return f"<ChatRoom {self.name or f'Direct-{self.id}'} type={self.room_type}>"

class ChatRoomMember(db.Model):
    """Participants d'une conversation"""
    __tablename__ = "chat_room_members"
    id = PK()
    room_id = FK("chat_rooms.id", nullable=False, ondelete="CASCADE", onupdate="CASCADE")
    user_id = FK("users.id", nullable=False, ondelete="CASCADE", onupdate="CASCADE")
    role = db.Column(db.Enum("member", "admin", "moderator", name="member_role"), nullable=False, default="member")
    joined_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    last_read_at = db.Column(db.DateTime, nullable=True)  # Pour marquer les messages comme lus
    is_muted = db.Column(db.Boolean, nullable=False, default=False)
    
    user = db.relationship("User", backref=db.backref("chat_memberships", lazy="select"))
    
    __table_args__ = (
        db.UniqueConstraint("room_id", "user_id", name="uq_room_member"),
        db.Index("idx_chatmember_room", "room_id"),
        db.Index("idx_chatmember_user", "user_id"),
        db.Index("idx_chatmember_lastread", "last_read_at"),
    )
    
    def __repr__(self):
        return f"<ChatRoomMember room={self.room_id} user={self.user_id} role={self.role}>"

class ChatMessage(db.Model):
    """Message dans une conversation"""
    __tablename__ = "chat_messages"
    id = PK()
    room_id = FK("chat_rooms.id", nullable=False, ondelete="CASCADE", onupdate="CASCADE")
    sender_id = FK("users.id", nullable=False, ondelete="RESTRICT", onupdate="CASCADE")
    content = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.Enum("text", "file", "system", name="message_type"), nullable=False, default="text")
    is_edited = db.Column(db.Boolean, nullable=False, default=False)
    edited_at = db.Column(db.DateTime, nullable=True)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)
    deleted_at = db.Column(db.DateTime, nullable=True)
    reply_to_id = FK("chat_messages.id", nullable=True, ondelete="SET NULL", onupdate="CASCADE")
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC), index=True)
    
    sender = db.relationship("User", backref=db.backref("chat_messages", lazy="select"))
    reply_to = db.relationship("ChatMessage", remote_side=[id], backref="replies")
    attachments = db.relationship("ChatAttachment", backref="message", cascade="all, delete-orphan", lazy="selectin")
    reads = db.relationship("ChatMessageRead", backref="message", cascade="all, delete-orphan", lazy="select")
    
    __table_args__ = (
        db.Index("idx_chatmsg_room", "room_id"),
        db.Index("idx_chatmsg_sender", "sender_id"),
        db.Index("idx_chatmsg_created", "created_at"),
        db.Index("idx_chatmsg_reply", "reply_to_id"),
        db.Index("idx_chatmsg_room_created", "room_id", "created_at"),  # Pour optimiser les requêtes
    )
    
    @property
    def unread_count(self):
        """Nombre d'utilisateurs qui n'ont pas lu ce message"""
        if not self.room or not self.room.members:
            return 0
        total_members = len([m for m in self.room.members if m.user_id != self.sender_id])
        read_count = len(self.reads)
        return max(0, total_members - read_count)
    
    def __repr__(self):
        return f"<ChatMessage {self.id} room={self.room_id} sender={self.sender_id}>"

class ChatAttachment(db.Model):
    """Pièce jointe d'un message"""
    __tablename__ = "chat_attachments"
    id = PK()
    message_id = FK("chat_messages.id", nullable=False, ondelete="CASCADE", onupdate="CASCADE")
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)  # Chemin relatif dans instance/uploads/chat/
    file_size = db.Column(BIGINT_U, nullable=False)  # Taille en octets
    file_type = db.Column(db.String(100), nullable=False)  # MIME type
    file_extension = db.Column(db.String(10), nullable=False)
    thumbnail_path = db.Column(db.String(500), nullable=True)  # Pour les images (miniature)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    
    __table_args__ = (
        db.Index("idx_chatattach_message", "message_id"),
        db.Index("idx_chatattach_type", "file_type"),
    )
    
    @property
    def is_image(self):
        """Vérifie si le fichier est une image"""
        return self.file_type.startswith('image/')
    
    @property
    def is_document(self):
        """Vérifie si le fichier est un document"""
        return self.file_type in ['application/pdf', 'application/msword', 
                                  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                                  'application/vnd.ms-excel',
                                  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']
    
    def __repr__(self):
        return f"<ChatAttachment {self.file_name} message={self.message_id}>"

class ChatMessageRead(db.Model):
    """Marqueurs de lecture des messages"""
    __tablename__ = "chat_message_reads"
    id = PK()
    message_id = FK("chat_messages.id", nullable=False, ondelete="CASCADE", onupdate="CASCADE")
    user_id = FK("users.id", nullable=False, ondelete="CASCADE", onupdate="CASCADE")
    read_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    
    user = db.relationship("User", backref=db.backref("chat_reads", lazy="select"))
    
    __table_args__ = (
        db.UniqueConstraint("message_id", "user_id", name="uq_msg_read"),
        db.Index("idx_chatread_message", "message_id"),
        db.Index("idx_chatread_user", "user_id"),
    )
    
    def __repr__(self):
        return f"<ChatMessageRead message={self.message_id} user={self.user_id}>"

# =========================================================
# MOTEUR DE RECHERCHE GLOBAL
# =========================================================

class SearchIndex(db.Model):
    """Index de recherche pour recherche full-text globale"""
    __tablename__ = "search_index"
    id = PK()
    entity_type = db.Column(db.String(50), nullable=False, index=True)  # 'article', 'simulation', 'forecast', etc.
    entity_id = db.Column(BIGINT_U, nullable=False, index=True)
    title = db.Column(db.String(500), nullable=False, index=True)
    content = db.Column(db.Text, nullable=True)  # Contenu indexé pour recherche full-text
    keywords = db.Column(db.String(1000), nullable=True)  # Mots-clés additionnels
    module = db.Column(db.String(50), nullable=False, index=True)  # 'stocks', 'simulations', 'forecast', etc.
    url = db.Column(db.String(500), nullable=True)  # URL pour accès direct
    search_metadata = db.Column(db.JSON, nullable=True)  # Métadonnées additionnelles (JSON)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC), index=True)
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(UTC), index=True)
    
    __table_args__ = (
        db.Index("idx_search_entity", "entity_type", "entity_id"),
        db.Index("idx_search_module", "module"),
        db.Index("idx_search_title", "title"),
        db.Index("idx_search_created", "created_at"),
    )
    
    def __repr__(self):
        return f"<SearchIndex {self.entity_type}:{self.entity_id} - {self.title[:50]}>"

# =========================================================
# ÉQUIPE DE PROMOTION - HOUSE TO HOUSE
# =========================================================

# Table de liaison many-to-many entre PromotionGamme et Article
promotion_gamme_articles = db.Table(
    'promotion_gamme_articles',
    db.Column('gamme_id', BIGINT_U, db.ForeignKey('promotion_gammes.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    db.Column('article_id', BIGINT_U, db.ForeignKey('articles.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True),
    db.Column('quantity', db.Integer, nullable=False, default=1),  # Quantité de l'article dans la gamme
    db.Column('created_at', db.DateTime, nullable=False, default=lambda: datetime.now(UTC)),
    db.Index('idx_gamme_article', 'gamme_id', 'article_id')
)

class PromotionGamme(db.Model):
    """Gammes de produits vendues par l'équipe de promotion"""
    __tablename__ = "promotion_gammes"
    id = PK()
    name = db.Column(db.String(200), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    is_piece = db.Column(db.Boolean, nullable=False, default=False)  # Indique si c'est une pièce/unitaire (ex: 1 bouteille)
    unit_type = db.Column(db.String(100), nullable=True)  # Type d'unité: "bouteille", "pièce", "sachet", "carton", etc.
    unit_description = db.Column(db.String(500), nullable=True)  # Description de l'unité: "800 ml", "1 kg", "500 g", etc.
    selling_price_gnf = db.Column(N18_2, nullable=False, default=Decimal("0.00"))  # Prix de vente (ex: 10 000 GNF)
    commission_per_unit_gnf = db.Column(N18_2, nullable=False, default=Decimal("0.00"))  # Commission par unité (ex: 1 500 GNF)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(UTC))
    
    sales = db.relationship("PromotionSale", backref="gamme", lazy="dynamic")
    articles = db.relationship("Article", secondary=promotion_gamme_articles, 
                               backref=db.backref("promotion_gammes", lazy="dynamic"),
                               lazy="select")
    
    __table_args__ = (
        db.Index("idx_promogamme_name", "name"),
        db.Index("idx_promogamme_active", "is_active"),
    )
    
    def __repr__(self):
        return f"<PromotionGamme {self.name} - {self.selling_price_gnf} GNF>"

class PromotionTeam(db.Model):
    """Équipes de promotion avec leur responsable"""
    __tablename__ = "promotion_teams"
    id = PK()
    name = db.Column(db.String(200), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    region = db.Column(db.String(100), nullable=True, index=True)  # Région d'activité de l'équipe
    team_leader_id = FK("users.id", nullable=False, onupdate="CASCADE", ondelete="RESTRICT")  # Responsable de groupe
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(UTC))
    
    team_leader = db.relationship("User", backref=db.backref("led_promotion_teams", lazy="select"))
    members = db.relationship("PromotionMember", backref="team", lazy="select", cascade="all, delete-orphan")
    
    __table_args__ = (
        db.Index("idx_promoteam_name", "name"),
        db.Index("idx_promoteam_leader", "team_leader_id"),
        db.Index("idx_promoteam_active", "is_active"),
    )
    
    def __repr__(self):
        return f"<PromotionTeam {self.name} - Leader: {self.team_leader_id}>"
    
    @property
    def members_count(self):
        """Nombre de membres actifs dans l'équipe"""
        return self.members.filter_by(is_active=True).count() if hasattr(self.members, 'filter_by') else len([m for m in self.members if m.is_active])

class PromotionMember(db.Model):
    """Membres de l'équipe de promotion (vendeurs house-to-house)"""
    __tablename__ = "promotion_members"
    id = PK()
    team_id = FK("promotion_teams.id", nullable=False, onupdate="CASCADE", ondelete="CASCADE")
    user_id = FK("users.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")  # Optionnel si pas d'utilisateur système
    full_name = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    gender = db.Column(db.Enum("M", "F", name="gender"), nullable=True)
    address = db.Column(db.String(500), nullable=True)
    # Géolocalisation du domicile
    home_latitude = db.Column(N18_4, nullable=True)  # Latitude du domicile
    home_longitude = db.Column(N18_4, nullable=True)  # Longitude du domicile
    # Intermédiaire/Responsable (référence à un autre membre)
    intermediaire_id = FK("promotion_members.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    joined_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    left_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(UTC))
    
    user = db.relationship("User", backref=db.backref("promotion_memberships", lazy="select"))
    sales = db.relationship("PromotionSale", backref="member", lazy="dynamic")
    intermediaire = db.relationship("PromotionMember", remote_side=[id], backref=db.backref("subordinates", lazy="dynamic"))
    
    __table_args__ = (
        db.Index("idx_promomember_team", "team_id"),
        db.Index("idx_promomember_user", "user_id"),
        db.Index("idx_promomember_name", "full_name"),
        db.Index("idx_promomember_phone", "phone"),
        db.Index("idx_promomember_active", "is_active"),
        db.Index("idx_promomember_intermediary", "intermediaire_id"),
        db.Index("idx_promomember_location", "home_latitude", "home_longitude"),
    )
    
    def __repr__(self):
        return f"<PromotionMember {self.full_name} - Team: {self.team_id}>"
    
    @property
    def total_sales_count(self):
        """Nombre total de ventes"""
        if hasattr(self.sales, 'count'):
            return self.sales.count()
        else:
            return len(list(self.sales))
    
    @property
    def total_commission_gnf(self):
        """Total des commissions gagnées"""
        from sqlalchemy import func
        result = db.session.query(func.sum(PromotionSale.commission_gnf)).filter_by(member_id=self.id).scalar()
        return result or Decimal("0.00")
    
    @property
    def has_location(self):
        """Vérifie si le membre a une géolocalisation"""
        return self.home_latitude is not None and self.home_longitude is not None

class PromotionSale(db.Model):
    """Ventes effectuées par les membres de l'équipe"""
    __tablename__ = "promotion_sales"
    id = PK()
    reference = db.Column(db.String(50), nullable=True, unique=True, index=True)  # Référence unique auto-générée
    member_id = FK("promotion_members.id", nullable=False, onupdate="CASCADE", ondelete="RESTRICT")
    gamme_id = FK("promotion_gammes.id", nullable=False, onupdate="CASCADE", ondelete="RESTRICT")
    transaction_type = db.Column(db.Enum("enlevement", "retour", name="transaction_type"), nullable=False, default="enlevement")  # Type de transaction
    quantity = db.Column(db.Integer, nullable=False, default=1)
    selling_price_gnf = db.Column(N18_2, nullable=False)  # Prix de vente unitaire
    total_amount_gnf = db.Column(N18_2, nullable=False)  # Montant total (quantity * selling_price)
    commission_per_unit_gnf = db.Column(N18_2, nullable=False)  # Commission par unité
    commission_gnf = db.Column(N18_2, nullable=False)  # Commission totale (quantity * commission_per_unit)
    sale_date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    customer_name = db.Column(db.String(200), nullable=True)
    customer_phone = db.Column(db.String(20), nullable=True)
    customer_address = db.Column(db.String(500), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    recorded_by_id = FK("users.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")  # Utilisateur qui a enregistré
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC), index=True)
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(UTC))
    
    recorded_by = db.relationship("User", backref=db.backref("recorded_promotion_sales", lazy="select"))
    
    __table_args__ = (
        db.Index("idx_promosale_member", "member_id"),
        db.Index("idx_promosale_gamme", "gamme_id"),
        db.Index("idx_promosale_date", "sale_date"),
        db.Index("idx_promosale_recorded", "recorded_by_id"),
        db.Index("idx_promosale_created", "created_at"),
        db.Index("idx_promosale_reference", "reference"),
        db.Index("idx_promosale_type", "transaction_type"),
    )
    
    def __repr__(self):
        return f"<PromotionSale Member:{self.member_id} Gamme:{self.gamme_id} Qty:{self.quantity} Date:{self.sale_date}>"

class PromotionReturn(db.Model):
    """Retours de gammes par les membres de l'équipe"""
    __tablename__ = "promotion_returns"
    id = PK()
    member_id = FK("promotion_members.id", nullable=False, onupdate="CASCADE", ondelete="RESTRICT")
    gamme_id = FK("promotion_gammes.id", nullable=False, onupdate="CASCADE", ondelete="RESTRICT")
    sale_id = FK("promotion_sales.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")  # Vente liée (optionnel)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    return_date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    reason = db.Column(db.String(500), nullable=True)  # Raison du retour
    status = db.Column(db.Enum("pending", "approved", "rejected", name="return_status"), nullable=False, default="pending")
    notes = db.Column(db.Text, nullable=True)
    approved_by_id = FK("users.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")  # Utilisateur qui a approuvé/refusé
    approved_at = db.Column(db.DateTime, nullable=True)
    recorded_by_id = FK("users.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")  # Utilisateur qui a enregistré
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC), index=True)
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(UTC))
    
    member = db.relationship("PromotionMember", backref=db.backref("returns", lazy="dynamic"))
    gamme = db.relationship("PromotionGamme", backref=db.backref("returns", lazy="dynamic"))
    sale = db.relationship("PromotionSale", backref=db.backref("returns", lazy="dynamic"))
    approved_by = db.relationship("User", foreign_keys=[approved_by_id], backref=db.backref("approved_promotion_returns", lazy="select"))
    recorded_by = db.relationship("User", foreign_keys=[recorded_by_id], backref=db.backref("recorded_promotion_returns", lazy="select"))
    
    __table_args__ = (
        db.Index("idx_promoreturn_member", "member_id"),
        db.Index("idx_promoreturn_gamme", "gamme_id"),
        db.Index("idx_promoreturn_sale", "sale_id"),
        db.Index("idx_promoreturn_date", "return_date"),
        db.Index("idx_promoreturn_status", "status"),
        db.Index("idx_promoreturn_created", "created_at"),
    )
    
    def __repr__(self):
        return f"<PromotionReturn Member:{self.member_id} Gamme:{self.gamme_id} Qty:{self.quantity} Status:{self.status}>"

class PromotionSupervisorStock(db.Model):
    """Stock central de gammes détenu par le superviseur/responsable promotion"""
    __tablename__ = "promotion_supervisor_stock"
    id = PK()
    supervisor_id = FK("users.id", nullable=False, onupdate="CASCADE", ondelete="CASCADE")  # Responsable promotion
    gamme_id = FK("promotion_gammes.id", nullable=False, onupdate="CASCADE", ondelete="CASCADE")
    quantity = db.Column(db.Integer, nullable=False, default=0)  # Quantité en stock actuelle
    last_updated = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    
    supervisor = db.relationship("User", backref=db.backref("supervisor_stocks", lazy="dynamic"))
    gamme = db.relationship("PromotionGamme", backref=db.backref("supervisor_stocks", lazy="dynamic"))
    
    __table_args__ = (
        db.UniqueConstraint("supervisor_id", "gamme_id", name="uq_supervisor_gamme_stock"),
        db.Index("idx_promosupervisorstock_supervisor", "supervisor_id"),
        db.Index("idx_promosupervisorstock_gamme", "gamme_id"),
        db.Index("idx_promosupervisorstock_updated", "last_updated"),
    )
    
    def __repr__(self):
        return f"<PromotionSupervisorStock Supervisor:{self.supervisor_id} Gamme:{self.gamme_id} Qty:{self.quantity}>"

class PromotionTeamStock(db.Model):
    """Stock de gammes détenu par chaque équipe de promotion"""
    __tablename__ = "promotion_team_stock"
    id = PK()
    team_id = FK("promotion_teams.id", nullable=False, onupdate="CASCADE", ondelete="CASCADE")
    gamme_id = FK("promotion_gammes.id", nullable=False, onupdate="CASCADE", ondelete="CASCADE")
    quantity = db.Column(db.Integer, nullable=False, default=0)  # Quantité en stock actuelle
    last_updated = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    
    team = db.relationship("PromotionTeam", backref=db.backref("stock_items", lazy="dynamic"))
    gamme = db.relationship("PromotionGamme", backref=db.backref("team_stocks", lazy="dynamic"))
    
    __table_args__ = (
        db.UniqueConstraint("team_id", "gamme_id", name="uq_team_gamme_stock"),
        db.Index("idx_promoteamstock_team", "team_id"),
        db.Index("idx_promoteamstock_gamme", "gamme_id"),
        db.Index("idx_promoteamstock_updated", "last_updated"),
    )
    
    def __repr__(self):
        return f"<PromotionTeamStock Team:{self.team_id} Gamme:{self.gamme_id} Qty:{self.quantity}>"

class PromotionMemberStock(db.Model):
    """Stock de gammes détenu par chaque membre de l'équipe promotion"""
    __tablename__ = "promotion_member_stock"
    id = PK()
    member_id = FK("promotion_members.id", nullable=False, onupdate="CASCADE", ondelete="CASCADE")
    gamme_id = FK("promotion_gammes.id", nullable=False, onupdate="CASCADE", ondelete="CASCADE")
    quantity = db.Column(db.Integer, nullable=False, default=0)  # Quantité en stock actuelle
    last_updated = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    
    member = db.relationship("PromotionMember", backref=db.backref("stock_items", lazy="dynamic"))
    gamme = db.relationship("PromotionGamme", backref=db.backref("member_stocks", lazy="dynamic"))
    
    __table_args__ = (
        db.UniqueConstraint("member_id", "gamme_id", name="uq_member_gamme_stock"),
        db.Index("idx_promostock_member", "member_id"),
        db.Index("idx_promostock_gamme", "gamme_id"),
        db.Index("idx_promostock_updated", "last_updated"),
    )
    
    def __repr__(self):
        return f"<PromotionMemberStock Member:{self.member_id} Gamme:{self.gamme_id} Qty:{self.quantity}>"

class PromotionStockMovement(db.Model):
    """Historique des mouvements de stock pour la promotion (superviseur, équipe, membre)"""
    __tablename__ = "promotion_stock_movements"
    id = PK()
    movement_type = db.Column(db.String(50), nullable=False)  # 'approvisionnement', 'distribution', 'enlevement', 'retour', 'affectation'
    movement_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC), index=True)
    
    # Source (d'où vient le stock)
    from_supervisor_id = FK("users.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")
    from_team_id = FK("promotion_teams.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")
    from_member_id = FK("promotion_members.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")
    
    # Destination (où va le stock)
    to_supervisor_id = FK("users.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")
    to_team_id = FK("promotion_teams.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")
    to_member_id = FK("promotion_members.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")
    
    gamme_id = FK("promotion_gammes.id", nullable=False, onupdate="CASCADE", ondelete="CASCADE")
    quantity = db.Column(db.Integer, nullable=False)  # Quantité positive (toujours)
    quantity_change = db.Column(db.Integer, nullable=False)  # Changement réel (+ ou -)
    
    # Référence à l'opération source (vente, retour, etc.)
    sale_id = FK("promotion_sales.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")
    return_id = FK("promotion_returns.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")
    
    # Utilisateur qui a effectué l'opération
    performed_by_id = FK("users.id", nullable=False, onupdate="CASCADE", ondelete="RESTRICT")
    
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    
    # Relations
    from_supervisor = db.relationship("User", foreign_keys=[from_supervisor_id], backref="promotion_movements_from_supervisor")
    to_supervisor = db.relationship("User", foreign_keys=[to_supervisor_id], backref="promotion_movements_to_supervisor")
    from_team = db.relationship("PromotionTeam", foreign_keys=[from_team_id], backref="promotion_movements_from_team")
    to_team = db.relationship("PromotionTeam", foreign_keys=[to_team_id], backref="promotion_movements_to_team")
    from_member = db.relationship("PromotionMember", foreign_keys=[from_member_id], backref="promotion_movements_from_member")
    to_member = db.relationship("PromotionMember", foreign_keys=[to_member_id], backref="promotion_movements_to_member")
    gamme = db.relationship("PromotionGamme", backref="stock_movements")
    sale = db.relationship("PromotionSale", backref="stock_movements")
    return_obj = db.relationship("PromotionReturn", backref="stock_movements")
    performed_by = db.relationship("User", foreign_keys=[performed_by_id], backref="promotion_movements_performed")
    
    __table_args__ = (
        db.Index("idx_promomovement_date", "movement_date"),
        db.Index("idx_promomovement_type", "movement_type"),
        db.Index("idx_promomovement_gamme", "gamme_id"),
        db.Index("idx_promomovement_from_supervisor", "from_supervisor_id"),
        db.Index("idx_promomovement_to_supervisor", "to_supervisor_id"),
        db.Index("idx_promomovement_from_team", "from_team_id"),
        db.Index("idx_promomovement_to_team", "to_team_id"),
        db.Index("idx_promomovement_from_member", "from_member_id"),
        db.Index("idx_promomovement_to_member", "to_member_id"),
    )
    
    def __repr__(self):
        return f"<PromotionStockMovement {self.movement_type} Gamme:{self.gamme_id} Qty:{self.quantity_change} Date:{self.movement_date}>"

class PromotionDailyClosure(db.Model):
    """Clôture quotidienne des opérations de promotion"""
    __tablename__ = "promotion_daily_closures"
    id = PK()
    closure_date = db.Column(db.Date, nullable=False, unique=True, index=True)
    closed_by_id = FK("users.id", nullable=False, onupdate="CASCADE", ondelete="RESTRICT")
    closed_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    notes = db.Column(db.Text, nullable=True)
    
    closed_by = db.relationship("User", backref=db.backref("daily_closures", lazy="dynamic"))
    
    __table_args__ = (
        db.Index("idx_closure_date", "closure_date"),
        db.Index("idx_closure_closed_by", "closed_by_id"),
    )
    
    def __repr__(self):
        return f"<PromotionDailyClosure Date:{self.closure_date} ClosedBy:{self.closed_by_id}>"

class PromotionMemberLocation(db.Model):
    """Positions géographiques des membres de l'équipe promotion (suivi des déplacements)"""
    __tablename__ = "promotion_member_locations"
    id = PK()
    member_id = FK("promotion_members.id", nullable=False, onupdate="CASCADE", ondelete="CASCADE")
    latitude = db.Column(N18_4, nullable=False)  # Latitude de la position
    longitude = db.Column(N18_4, nullable=False)  # Longitude de la position
    address = db.Column(db.String(500), nullable=True)  # Adresse correspondante (optionnel)
    activity_type = db.Column(db.String(50), nullable=True)  # Type d'activité: "vente", "visite", "retour", etc.
    notes = db.Column(db.Text, nullable=True)  # Notes sur la position
    recorded_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC), index=True)
    recorded_by_id = FK("users.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")  # Qui a enregistré
    
    member = db.relationship("PromotionMember", backref=db.backref("locations", lazy="dynamic"))
    recorded_by = db.relationship("User", backref=db.backref("recorded_promotion_locations", lazy="select"))
    
    __table_args__ = (
        db.Index("idx_promoloc_member", "member_id"),
        db.Index("idx_promoloc_recorded", "recorded_at"),
        db.Index("idx_promoloc_coords", "latitude", "longitude"),
        db.Index("idx_promoloc_activity", "activity_type"),
    )
    
    def __repr__(self):
        return f"<PromotionMemberLocation Member:{self.member_id} Lat:{self.latitude} Lon:{self.longitude} At:{self.recorded_at}>"

# =========================================================
# RAPPORTS AUTOMATIQUES
# =========================================================

class ScheduledReport(db.Model):
    """Configuration de rapports automatiques à envoyer via WhatsApp"""
    __tablename__ = "scheduled_reports"
    id = PK()
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    report_type = db.Column(db.Enum("stock_inventory", "stock_summary", "order_summary", name="report_type_enum"), 
                            nullable=False, index=True)
    schedule_type = db.Column(db.Enum("daily", "weekly", "monthly", name="schedule_type_enum"), 
                             nullable=False, default="daily")
    schedule = db.Column(db.String(50), nullable=False)  # Format: "HH:MM" pour daily, "DAY HH:MM" pour weekly
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    
    # Paramètres du rapport
    depot_id = FK("depots.id", nullable=True, onupdate="CASCADE", ondelete="SET NULL")
    period = db.Column(db.String(50), nullable=True, default="all")  # all, today, week, month, year, custom
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    currency = db.Column(db.String(10), nullable=False, default="GNF")
    
    # Destinataires WhatsApp
    whatsapp_account_id = db.Column(db.String(100), nullable=False)  # ID du compte WhatsApp Message Pro
    recipients = db.Column(db.Text, nullable=True)  # Numéros séparés par des virgules
    group_ids = db.Column(db.Text, nullable=True)  # IDs de groupes séparés par des virgules
    message = db.Column(db.Text, nullable=True)  # Message personnalisé à envoyer avec le rapport
    
    # Suivi d'exécution
    last_run = db.Column(db.DateTime, nullable=True)
    next_run = db.Column(db.DateTime, nullable=True)
    run_count = db.Column(db.Integer, nullable=False, default=0)
    last_error = db.Column(db.Text, nullable=True)
    
    # Métadonnées
    created_by_id = FK("users.id", nullable=False, onupdate="CASCADE", ondelete="RESTRICT")
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(UTC))
    
    created_by = db.relationship("User", foreign_keys=[created_by_id], lazy="joined")
    depot = db.relationship("Depot", lazy="joined")
    
    __table_args__ = (
        db.Index("idx_scheduledreport_type", "report_type"),
        db.Index("idx_scheduledreport_active", "is_active"),
        db.Index("idx_scheduledreport_nextrun", "next_run"),
    )
    
    def __repr__(self):
        return f"<ScheduledReport {self.name} ({self.report_type})>"
