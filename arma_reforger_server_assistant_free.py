#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARMA REFORGER SERVER ASSISTANT - VERSION FREE
------------------------------------------------
Logiciel tout-en-un pour installer, configurer et lancer un serveur dédié
Arma Reforger, sans rien connaître à SteamCMD ni au JSON.

© JAVIDI STUDIO

Version FREE 2026 (gratuite) :
    - Installation "1 clic" de SteamCMD + du serveur, avec vérification
      réelle de chaque sous-étape, tentatives automatiques et messages
      rassurants pendant les phases longues (téléchargement, extraction).
    - MÉMOIRE PERSISTANTE : les dossiers d'installation et la configuration
      sont sauvegardés entre les sessions (settings.json).
      Au démarrage, l'application détecte automatiquement une installation
      existante et valide les étapes correspondantes.
    - Options avancées : App ID Steam personnalisable, branche bêta,
      URL SteamCMD modifiable (ces identifiants peuvent évoluer).
    - Génération simple du config.json + du .bat de lancement
    - Lancement / arrêt du serveur
    - Bouton "Signaler un problème" qui génère un rapport exploitable
    - Publicité toutes les 5 minutes (une seule fenêtre à la fois,
      le compteur repart de zéro à la fermeture de la publicité)

Non inclus dans la FREE (réservé à la PREMIUM — http://javidistudio.fr) :
    - Gestion des mods en 1 clic (ajout, mise à jour automatique,
      presets, ordre de chargement)
    - Diagnostic de ports / firewall
    - Profils serveur multiples, rapports exportables avancés

Note : les ID de scénarios et l'App ID SteamCMD peuvent changer avec le
temps ; c'est justement pour cela que l'App ID est modifiable dans les
options avancées de l'étape 1. Vérifiez la documentation / le wiki
communautaire Arma Reforger si un identifiant ne fonctionne plus.
"""

import os
import sys
import json
import time
import random
import socket
import queue
import zipfile
import platform
import datetime
import threading
import subprocess
import webbrowser
import urllib.request
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# --------------------------------------------------------------------------
# CONSTANTES
# --------------------------------------------------------------------------

APP_TITLE = 'ARMA REFORGER SERVER ASSISTANT — VERSION FREE 2026'
APP_VERSION = "2026.1.0-free"
COMPANY_NAME = "JAVIDI STUDIO"

# Site officiel JAVIDI STUDIO : téléchargement de la version PREMIUM
PREMIUM_URL = "http://javidistudio.fr"

# Lien d'affiliation Shockbyte (-25 % pour les utilisateurs qui passent par ce lien)
AFFILIATE_URL = "https://shockbyte.com/billing/aff.php?aff=11359"
SHOCKBYTE_BLUE = "#2275ff"
SHOCKBYTE_CYAN = "#18f2f8"

# Valeurs PAR DÉFAUT — modifiables dans les options avancées de l'étape 1,
# car ces identifiants peuvent évoluer dans le temps.
DEFAULT_STEAMCMD_ZIP_URL = "https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip"
DEFAULT_REFORGER_SERVER_APPID = "1874900"  # AppID SteamCMD du serveur dédié stable

# Publicité : intervalle entre deux affichages (le compteur repart de zéro
# à la fermeture de la fenêtre de pub, pas à son ouverture).
AD_INTERVAL_MS = 5 * 60 * 1000  # 5 minutes

# Fichier de sauvegarde des réglages (dossiers, config, mods, étapes validées)
def _settings_dir():
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    else:
        base = os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(base, "ArmaReforgerAssistant")


SETTINGS_PATH = os.path.join(_settings_dir(), "settings.json")

SCENARIO_PRESETS = {
    "Conflict - Everon (par défaut)": "{ECC61978EDCC2B5A}Missions/23_Campaign.conf",
    "Personnalisé (je saisis l'ID moi-même)": "",
}

# Palette de couleurs "conviviale mais pro"
COLOR_BG = "#11151c"
COLOR_BG_PANEL = "#1a2029"
COLOR_BG_CARD = "#212a36"
COLOR_ACCENT_GREEN = "#3ddc84"
COLOR_ACCENT_ORANGE = "#ff9f1c"
COLOR_ACCENT_RED = "#ff5c5c"
COLOR_TEXT = "#f2f4f8"
COLOR_TEXT_DIM = "#8a93a3"
COLOR_LOCKED = "#3a4150"

FONT_TITLE = ("Segoe UI", 20, "bold")
FONT_SUB = ("Segoe UI", 11)
FONT_STEP = ("Segoe UI", 12, "bold")
FONT_NORMAL = ("Segoe UI", 10)
FONT_BUTTON = ("Segoe UI", 11, "bold")

NO_WINDOW_FLAG = getattr(subprocess, "CREATE_NO_WINDOW", 0)

# Nouvelle numérotation : Installation (SteamCMD+Serveur fusionnés) / Config / Mods / Lancer
STEPS = [
    "1. Installation",
    "2. Configuration",
    "3. Mods",
    "4. Lancer",
]

CHECKLIST_STEPS = [
    ("prepare", "Préparer les dossiers"),
    ("steamcmd", "Installer / vérifier SteamCMD"),
    ("server", "Installer / mettre à jour le serveur"),
    ("verify", "Vérification finale des fichiers"),
]

WATCHDOG_SILENCE_SECONDS = 30  # au-delà, on rassure l'utilisateur
STALL_HARD_LIMIT_SECONDS = 900  # 15 min sans rien : on prévient que c'est long


# --------------------------------------------------------------------------
# OUTILS RESEAU / SYSTEME
# --------------------------------------------------------------------------

def detect_local_ip():
    """Retourne l'adresse IP locale de la machine (best effort)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def detect_public_ip():
    """Retourne l'adresse IP publique (best effort, nécessite internet)."""
    try:
        with urllib.request.urlopen("https://api.ipify.org", timeout=5) as r:
            return r.read().decode().strip()
    except Exception:
        return ""


def folder_size_mb(path):
    """Taille totale d'un dossier en Mo (best effort, ne plante jamais)."""
    total = 0
    try:
        for root, _dirs, files in os.walk(path):
            for name in files:
                try:
                    total += os.path.getsize(os.path.join(root, name))
                except OSError:
                    pass
    except OSError:
        pass
    return round(total / (1024 * 1024), 1)


# --------------------------------------------------------------------------
# SAUVEGARDE / CHARGEMENT DES REGLAGES (mémoire persistante)
# --------------------------------------------------------------------------

def load_settings():
    """Charge les réglages sauvegardés (dossiers, config, mods...).
    Retourne un dict (vide si aucun fichier ou fichier corrompu)."""
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except (OSError, json.JSONDecodeError):
        pass
    return {}


def save_settings(data):
    """Sauvegarde les réglages sur disque (best effort, ne plante jamais)."""
    try:
        os.makedirs(_settings_dir(), exist_ok=True)
        # Écriture atomique : on écrit dans un fichier temporaire puis on
        # remplace, pour ne jamais corrompre settings.json si l'app est
        # fermée brutalement en pleine écriture.
        tmp_path = SETTINGS_PATH + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        os.replace(tmp_path, SETTINGS_PATH)
        return True
    except OSError:
        return False


# --------------------------------------------------------------------------
# APPLICATION PRINCIPALE
# --------------------------------------------------------------------------

class ArmaAssistantFree(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title(APP_TITLE)
        self.geometry("1000x720")
        self.minsize(920, 640)
        self.configure(bg=COLOR_BG)

        # état de progression : True si l'étape est validée
        # 1 = Installation, 2 = Config, 3 = Mods (vitrine PREMIUM), 4 = Lancer
        self.step_done = {1: False, 2: False, 3: True, 4: False}
        self.current_step = 1

        # --- Chargement des réglages sauvegardés (mémoire persistante) ---
        saved = load_settings()

        # variables Tkinter (initialisées avec les valeurs sauvegardées si présentes)
        self.steamcmd_dir = tk.StringVar(
            value=saved.get("steamcmd_dir") or os.path.join(os.path.expanduser("~"), "SteamCMD"))
        self.server_dir = tk.StringVar(
            value=saved.get("server_dir") or os.path.join(os.path.expanduser("~"), "ArmaReforgerServer"))
        self.server_name = tk.StringVar(value=saved.get("server_name") or "Mon serveur Arma Reforger")
        self.server_password = tk.StringVar(value=saved.get("server_password") or "")
        self.server_password_admin = tk.StringVar(value=saved.get("server_password_admin") or "gameMaster")
        self.max_players = tk.IntVar(value=int(saved.get("max_players") or 32))
        self.scenario_choice = tk.StringVar(
            value=saved.get("scenario_choice") or list(SCENARIO_PRESETS.keys())[0])
        self.scenario_custom = tk.StringVar(value=saved.get("scenario_custom") or "")
        self.public_ip = tk.StringVar(value=saved.get("public_ip") or "")
        self.local_ip = tk.StringVar(value=detect_local_ip())
        self.server_port = tk.IntVar(value=int(saved.get("server_port") or 2001))

        # --- Options avancées : identifiants Steam modifiables (Build/App ID) ---
        # Ces valeurs peuvent évoluer dans le temps côté Steam / Bohemia,
        # d'où la possibilité de les saisir manuellement.
        self.server_appid_var = tk.StringVar(
            value=saved.get("server_appid") or DEFAULT_REFORGER_SERVER_APPID)
        self.beta_branch_var = tk.StringVar(value=saved.get("beta_branch") or "")
        self.steamcmd_url_var = tk.StringVar(
            value=saved.get("steamcmd_url") or DEFAULT_STEAMCMD_ZIP_URL)

        self.server_process = None
        self.log_queue = queue.Queue()
        self.full_log_history = []

        self.step_buttons = {}
        self.step_frames = {}
        self.checklist_labels = {}
        self.install_running = False

        # Publicité : référence de la fenêtre en cours + id du minuteur,
        # pour garantir UNE SEULE fenêtre à la fois et pouvoir remettre
        # le compteur à zéro à la fermeture.
        self.ad_window = None
        self._ad_after_id = None

        self._build_ui()
        self._poll_log_queue()
        self._schedule_ad()

        # Auto-détection d'une installation existante APRES construction de
        # l'UI (corrige le bug : l'app redemandait d'installer SteamCMD et
        # le serveur à chaque lancement alors qu'ils étaient déjà là).
        self.after(300, self._auto_detect_existing_install)

    # ------------------------------------------------------------------
    # MEMOIRE PERSISTANTE : sauvegarde + auto-détection au démarrage
    # ------------------------------------------------------------------

    def _collect_settings(self):
        return {
            "app_version": APP_VERSION,
            "steamcmd_dir": self.steamcmd_dir.get().strip(),
            "server_dir": self.server_dir.get().strip(),
            "server_name": self.server_name.get(),
            "server_password": self.server_password.get(),
            "server_password_admin": self.server_password_admin.get(),
            "max_players": self._get_int(self.max_players, 32),
            "scenario_choice": self.scenario_choice.get(),
            "scenario_custom": self.scenario_custom.get(),
            "public_ip": self.public_ip.get().strip(),
            "server_port": self._get_int(self.server_port, 2001),
            "server_appid": self.server_appid_var.get().strip(),
            "beta_branch": self.beta_branch_var.get().strip(),
            "steamcmd_url": self.steamcmd_url_var.get().strip(),
        }

    def _save_settings(self):
        if save_settings(self._collect_settings()):
            self._log("💾 Réglages sauvegardés (dossiers, configuration, mods).")
        else:
            self._log("⚠️ Impossible de sauvegarder les réglages sur le disque.")

    def _auto_detect_existing_install(self):
        """Au démarrage, vérifie si SteamCMD et le serveur sont déjà installés
        dans les dossiers mémorisés, et valide automatiquement les étapes
        correspondantes pour ne PAS redemander l'installation."""
        steamcmd_ok = os.path.isfile(os.path.join(self.steamcmd_dir.get().strip(), "steamcmd.exe"))
        server_exe = os.path.join(self.server_dir.get().strip(), "ArmaReforgerServer.exe")
        server_ok = os.path.isfile(server_exe) and os.path.getsize(server_exe) > 1_000_000

        if steamcmd_ok and server_ok:
            self.step_done[1] = True
            self._set_checklist_state("prepare", "done")
            self._set_checklist_state("steamcmd", "done")
            self._set_checklist_state("server", "done")
            self._set_checklist_state("verify", "done")
            self._set_steamcmd_status("✅ SteamCMD déjà installé (détecté au démarrage)", COLOR_ACCENT_GREEN)
            self._set_server_status("✅ Serveur déjà installé (détecté au démarrage)", COLOR_ACCENT_GREEN)
            self._log("✅ Installation existante détectée : SteamCMD et le serveur sont déjà en place, "
                      "pas besoin de réinstaller. (Le bouton 1-clic reste utilisable pour mettre à jour.)")
        elif steamcmd_ok:
            self._set_steamcmd_status("✅ SteamCMD déjà installé (détecté au démarrage)", COLOR_ACCENT_GREEN)
            self._log("ℹ️ SteamCMD détecté, mais pas le serveur : utilise le bouton 1-clic pour terminer.")

        config_path = os.path.join(self.server_dir.get().strip(), "configs", "config.json")
        if self.step_done[1] and os.path.isfile(config_path):
            self.step_done[2] = True
            self._log(f"✅ Configuration existante détectée : {config_path}")
            self.config_status_label.config(
                text="✅ Configuration existante détectée au démarrage", fg=COLOR_ACCENT_GREEN)

        self._refresh_sidebar()

    @staticmethod
    def _get_int(var, default):
        """Lit un IntVar sans planter si le champ a été vidé par l'utilisateur
        (tk.TclError sinon), et retourne la valeur par défaut si invalide."""
        try:
            return int(var.get())
        except (tk.TclError, ValueError):
            return default

    # ------------------------------------------------------------------
    # CONSTRUCTION DE L'INTERFACE
    # ------------------------------------------------------------------

    def _build_ui(self):
        header = tk.Frame(self, bg=COLOR_BG_PANEL, height=90)
        header.pack(side="top", fill="x")
        header.pack_propagate(False)

        tk.Label(
            header, text="🎖️  ARMA REFORGER SERVER ASSISTANT",
            font=FONT_TITLE, bg=COLOR_BG_PANEL, fg=COLOR_ACCENT_GREEN,
        ).pack(anchor="w", padx=24, pady=(14, 0))
        tk.Label(
            header,
            text=f'Version FREE 2026 — installation en 1 clic, configuration et lancement guidés  •  © {COMPANY_NAME}',
            font=FONT_SUB, bg=COLOR_BG_PANEL, fg=COLOR_TEXT_DIM,
        ).pack(anchor="w", padx=24)

        # --- Bannière partenaire Shockbyte (lien d'affiliation, -25 %) ---
        self._build_affiliate_banner()

        body = tk.Frame(self, bg=COLOR_BG)
        body.pack(side="top", fill="both", expand=True)

        # --- Barre latérale (les étapes) ---
        sidebar = tk.Frame(body, bg=COLOR_BG_PANEL, width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(
            sidebar, text="ÉTAPES", font=("Segoe UI", 10, "bold"),
            bg=COLOR_BG_PANEL, fg=COLOR_TEXT_DIM,
        ).pack(anchor="w", padx=18, pady=(20, 6))

        for i, label in enumerate(STEPS, start=1):
            btn = tk.Button(
                sidebar, text=label, font=FONT_STEP, anchor="w",
                bd=0, relief="flat", padx=18, pady=12,
                command=lambda i=i: self._go_to_step(i),
            )
            btn.pack(fill="x", padx=10, pady=3)
            self.step_buttons[i] = btn

        tk.Label(sidebar, text="", bg=COLOR_BG_PANEL).pack(expand=True, fill="both")

        tk.Button(
            sidebar, text="🐞  Signaler un problème", font=("Segoe UI", 9, "bold"),
            bg=COLOR_BG_CARD, fg=COLOR_TEXT, bd=0, relief="flat",
            padx=10, pady=8, cursor="hand2",
            command=self._on_report_problem,
        ).pack(fill="x", padx=10, pady=(0, 8))

        pro_frame = tk.Frame(sidebar, bg=COLOR_BG_CARD)
        pro_frame.pack(fill="x", padx=10, pady=(0, 16))
        tk.Label(
            pro_frame, text="⭐ Version PREMIUM", font=("Segoe UI", 11, "bold"),
            bg=COLOR_BG_CARD, fg=COLOR_ACCENT_ORANGE,
        ).pack(anchor="w", padx=10, pady=(10, 0))
        tk.Label(
            pro_frame, text="Sans pub, mods en 1 clic,\nscénarios avancés...",
            font=("Segoe UI", 9), bg=COLOR_BG_CARD, fg=COLOR_TEXT_DIM, justify="left",
        ).pack(anchor="w", padx=10, pady=(2, 10))
        tk.Button(
            pro_frame, text="⬇ Télécharger", font=("Segoe UI", 9, "bold"),
            bg=COLOR_ACCENT_ORANGE, fg="#1a1300", bd=0, relief="flat", cursor="hand2",
            command=self._open_premium_link,
        ).pack(fill="x", padx=10, pady=(0, 4))
        tk.Button(
            pro_frame, text="En savoir plus", font=("Segoe UI", 9),
            bg=COLOR_BG_PANEL, fg=COLOR_TEXT_DIM, bd=0, relief="flat", cursor="hand2",
            command=self._show_pro_popup,
        ).pack(fill="x", padx=10, pady=(0, 10))

        # --- Zone principale : contenu de l'étape ---
        main = tk.Frame(body, bg=COLOR_BG)
        main.pack(side="left", fill="both", expand=True)

        self.content_container = tk.Frame(main, bg=COLOR_BG)
        self.content_container.pack(side="top", fill="both", expand=True, padx=24, pady=20)

        self.step_frames[1] = self._build_step_install(self.content_container)
        self.step_frames[2] = self._build_step_config(self.content_container)
        self.step_frames[3] = self._build_step_mods(self.content_container)
        self.step_frames[4] = self._build_step_launch(self.content_container)

        # --- Journal en bas ---
        log_panel = tk.Frame(main, bg=COLOR_BG_PANEL, height=160)
        log_panel.pack(side="bottom", fill="x")
        log_panel.pack_propagate(False)
        tk.Label(
            log_panel, text="Journal", font=("Segoe UI", 9, "bold"),
            bg=COLOR_BG_PANEL, fg=COLOR_TEXT_DIM,
        ).pack(anchor="w", padx=14, pady=(8, 0))
        self.log_text = tk.Text(
            log_panel, height=7, bg="#0b0e13", fg=COLOR_TEXT,
            font=("Consolas", 9), bd=0, relief="flat", wrap="word",
        )
        self.log_text.pack(fill="both", expand=True, padx=14, pady=(2, 10))
        self.log_text.configure(state="disabled")

        self._refresh_sidebar()
        self._go_to_step(1)

    # ------------------------------------------------------------------
    # BANNIERE PARTENAIRE SHOCKBYTE (lien d'affiliation)
    # ------------------------------------------------------------------
    # Note : Tkinter ne sait pas afficher de SVG nativement, la bannière
    # reprend donc les couleurs du logo Shockbyte (bleu #2275ff / cyan)
    # avec un éclair, plutôt que le fichier SVG officiel.

    def _build_affiliate_banner(self):
        banner = tk.Frame(self, bg=SHOCKBYTE_BLUE, cursor="hand2")
        banner.pack(side="top", fill="x")

        inner = tk.Frame(banner, bg=SHOCKBYTE_BLUE)
        inner.pack(padx=24, pady=6, fill="x")

        logo = tk.Label(
            inner, text="⚡ SHOCKBYTE", font=("Segoe UI", 12, "bold"),
            bg=SHOCKBYTE_BLUE, fg="#ffffff",
        )
        logo.pack(side="left")

        msg = tk.Label(
            inner,
            text="Marre que votre ordinateur rame avec votre serveur hébergé chez vous ? "
                 "Faites confiance à Shockbyte : hébergement pro, -25 % via notre lien !",
            font=("Segoe UI", 10), bg=SHOCKBYTE_BLUE, fg="#eaf3ff", anchor="w",
        )
        msg.pack(side="left", padx=(14, 8), fill="x", expand=True)

        cta = tk.Label(
            inner, text="Créer mon serveur ➜", font=("Segoe UI", 10, "bold"),
            bg=SHOCKBYTE_CYAN, fg="#062a3a", padx=12, pady=3,
        )
        cta.pack(side="right")

        # Toute la bannière est cliquable
        for widget in (banner, inner, logo, msg, cta):
            widget.bind("<Button-1>", lambda _e: self._open_affiliate_link())
            widget.configure(cursor="hand2")

    def _open_affiliate_link(self):
        try:
            webbrowser.open(AFFILIATE_URL)
            self._log("🌐 Ouverture du lien partenaire Shockbyte (-25 %)...")
        except Exception as e:
            self._log(f"⚠️ Impossible d'ouvrir le navigateur : {e}")

    # ------------------------------------------------------------------
    # CARTE GENERIQUE POUR CHAQUE ETAPE
    # ------------------------------------------------------------------

    def _card(self, parent, title, subtitle=""):
        frame = tk.Frame(parent, bg=COLOR_BG)
        tk.Label(
            frame, text=title, font=("Segoe UI", 16, "bold"),
            bg=COLOR_BG, fg=COLOR_TEXT,
        ).pack(anchor="w")
        if subtitle:
            tk.Label(
                frame, text=subtitle, font=FONT_NORMAL,
                bg=COLOR_BG, fg=COLOR_TEXT_DIM, wraplength=680, justify="left",
            ).pack(anchor="w", pady=(2, 14))
        else:
            tk.Frame(frame, bg=COLOR_BG, height=10).pack()
        card = tk.Frame(frame, bg=COLOR_BG_CARD, padx=20, pady=20)
        card.pack(fill="both", expand=True, pady=(6, 0))
        return frame, card

    def _labeled_entry(self, parent, label, textvariable, browse=False):
        line = tk.Frame(parent, bg=COLOR_BG_CARD)
        line.pack(fill="x", pady=6)
        tk.Label(
            line, text=label, font=FONT_NORMAL, bg=COLOR_BG_CARD, fg=COLOR_TEXT,
            width=22, anchor="w",
        ).pack(side="left")
        entry = tk.Entry(
            line, textvariable=textvariable, font=FONT_NORMAL,
            bg="#101620", fg=COLOR_TEXT, insertbackground=COLOR_TEXT,
            relief="flat",
        )
        entry.pack(side="left", fill="x", expand=True, ipady=4, padx=(0, 8))
        if browse:
            tk.Button(
                line, text="Parcourir...", font=("Segoe UI", 9),
                bg=COLOR_BG_PANEL, fg=COLOR_TEXT, bd=0, relief="flat",
                command=lambda: self._browse_folder(textvariable),
            ).pack(side="left")
        return entry

    def _browse_folder(self, var):
        chosen = filedialog.askdirectory(initialdir=var.get() or os.path.expanduser("~"))
        if chosen:
            var.set(chosen)

    def _action_button(self, parent, text, command, color=COLOR_ACCENT_GREEN, fg="#08240f"):
        return tk.Button(
            parent, text=text, font=FONT_BUTTON, bg=color, fg=fg,
            bd=0, relief="flat", padx=18, pady=10, cursor="hand2",
            command=command,
        )

    # ------------------------------------------------------------------
    # ETAPE 1 : INSTALLATION (SteamCMD + Serveur, en 1 clic)
    # ------------------------------------------------------------------

    def _build_step_install(self, parent):
        frame, card = self._card(
            parent, "Étape 1 — Installation",
            "En appuyant sur le bouton « Tout installer en 1 clic », "
            "vous installerez SteamCMD et Arma Reforger Server.",
        )

        self._labeled_entry(card, "Dossier SteamCMD :", self.steamcmd_dir, browse=True)
        self._labeled_entry(card, "Dossier du serveur :", self.server_dir, browse=True)

        tk.Frame(card, bg=COLOR_BG_CARD, height=8).pack()

        self.one_click_btn = self._action_button(
            card, "🚀  Tout installer en 1 clic", self._on_one_click_install,
        )
        self.one_click_btn.pack(anchor="w", pady=(4, 16))

        # --- Checklist en direct ---
        checklist_frame = tk.Frame(card, bg=COLOR_BG_CARD)
        checklist_frame.pack(fill="x", pady=(0, 6))
        for key, label in CHECKLIST_STEPS:
            row = tk.Frame(checklist_frame, bg=COLOR_BG_CARD)
            row.pack(fill="x", pady=3)
            icon_lbl = tk.Label(
                row, text="⬜", font=("Segoe UI", 12), bg=COLOR_BG_CARD,
                fg=COLOR_TEXT_DIM, width=3,
            )
            icon_lbl.pack(side="left")
            text_lbl = tk.Label(
                row, text=label, font=FONT_NORMAL, bg=COLOR_BG_CARD,
                fg=COLOR_TEXT, anchor="w",
            )
            text_lbl.pack(side="left", fill="x", expand=True)
            self.checklist_labels[key] = (icon_lbl, text_lbl)

        self.install_progress = ttk.Progressbar(card, mode="indeterminate")
        self.install_progress.pack(fill="x", pady=(10, 4))

        self.install_elapsed_label = tk.Label(
            card, text="", font=("Segoe UI", 9), bg=COLOR_BG_CARD, fg=COLOR_TEXT_DIM,
        )
        self.install_elapsed_label.pack(anchor="w")

        # --- Section avancée : contrôle manuel étape par étape ---
        adv_toggle = tk.Button(
            card, text="⚙️  Options avancées (installer séparément)",
            font=("Segoe UI", 9, "underline"), bg=COLOR_BG_CARD, fg=COLOR_TEXT_DIM,
            bd=0, relief="flat", cursor="hand2", anchor="w",
            command=self._toggle_advanced_install,
        )
        adv_toggle.pack(anchor="w", pady=(16, 4))

        self.advanced_frame = tk.Frame(card, bg=COLOR_BG_CARD)
        # caché par défaut, affiché via _toggle_advanced_install

        # --- Identifiants Steam personnalisables (peuvent évoluer dans le temps) ---
        tk.Label(
            self.advanced_frame,
            text="Identifiants Steam personnalisés (à modifier uniquement si les valeurs "
                 "par défaut ne fonctionnent plus, elles peuvent évoluer avec le temps) :",
            font=("Segoe UI", 9), bg=COLOR_BG_CARD, fg=COLOR_TEXT_DIM,
            wraplength=640, justify="left",
        ).pack(anchor="w", pady=(0, 6))

        self._labeled_entry(self.advanced_frame, "App ID du serveur :", self.server_appid_var)
        self._labeled_entry(self.advanced_frame, "Branche bêta (optionnel) :", self.beta_branch_var)
        self._labeled_entry(self.advanced_frame, "URL SteamCMD (.zip) :", self.steamcmd_url_var)

        reset_row = tk.Frame(self.advanced_frame, bg=COLOR_BG_CARD)
        reset_row.pack(fill="x", pady=(2, 10))
        tk.Button(
            reset_row, text="↩ Rétablir les valeurs par défaut", font=("Segoe UI", 9),
            bg=COLOR_BG_PANEL, fg=COLOR_TEXT_DIM, bd=0, relief="flat", cursor="hand2",
            command=self._reset_steam_ids,
        ).pack(anchor="w")

        row1 = tk.Frame(self.advanced_frame, bg=COLOR_BG_CARD)
        row1.pack(fill="x", pady=4)
        self._action_button(
            row1, "Installer / vérifier SteamCMD seul", self._on_install_steamcmd_only,
            color=COLOR_BG_PANEL, fg=COLOR_TEXT,
        ).pack(side="left", padx=(0, 10))
        self._action_button(
            row1, "Installer / mettre à jour le serveur seul", self._on_install_server_only,
            color=COLOR_BG_PANEL, fg=COLOR_TEXT,
        ).pack(side="left")

        self.steamcmd_status_label = tk.Label(
            self.advanced_frame, text="Statut SteamCMD : non vérifié", font=FONT_NORMAL,
            bg=COLOR_BG_CARD, fg=COLOR_TEXT_DIM,
        )
        self.steamcmd_status_label.pack(anchor="w", pady=(10, 2))
        self.server_status_label = tk.Label(
            self.advanced_frame, text="Statut serveur : non installé", font=FONT_NORMAL,
            bg=COLOR_BG_CARD, fg=COLOR_TEXT_DIM,
        )
        self.server_status_label.pack(anchor="w")

        return frame

    def _reset_steam_ids(self):
        self.server_appid_var.set(DEFAULT_REFORGER_SERVER_APPID)
        self.beta_branch_var.set("")
        self.steamcmd_url_var.set(DEFAULT_STEAMCMD_ZIP_URL)
        self._log("↩ Identifiants Steam rétablis aux valeurs par défaut.")

    def _get_server_appid(self):
        """Retourne l'App ID saisi si valide (chiffres uniquement),
        sinon la valeur par défaut avec un avertissement."""
        appid = self.server_appid_var.get().strip()
        if appid.isdigit():
            return appid
        self._log(f"⚠️ App ID invalide (« {appid} »), utilisation de la valeur "
                  f"par défaut {DEFAULT_REFORGER_SERVER_APPID}.")
        return DEFAULT_REFORGER_SERVER_APPID

    def _toggle_advanced_install(self):
        if self.advanced_frame.winfo_ismapped():
            self.advanced_frame.pack_forget()
        else:
            self.advanced_frame.pack(fill="x", pady=(4, 0))

    # --- checklist helpers -------------------------------------------------

    def _reset_checklist(self):
        for key, _ in CHECKLIST_STEPS:
            self._set_checklist_state(key, "pending")

    def _set_checklist_state(self, key, state):
        icons = {
            "pending": ("⬜", COLOR_TEXT_DIM),
            "in_progress": ("⏳", COLOR_ACCENT_ORANGE),
            "done": ("✅", COLOR_ACCENT_GREEN),
            "failed": ("❌", COLOR_ACCENT_RED),
        }
        icon, color = icons[state]
        icon_lbl, text_lbl = self.checklist_labels[key]

        def apply():
            icon_lbl.config(text=icon, fg=color)
            text_lbl.config(fg=color if state == "failed" else COLOR_TEXT)

        self.after(0, apply)

    # --- 1-clic -------------------------------------------------------------

    def _on_one_click_install(self):
        if self.install_running:
            return
        steamcmd_path = self.steamcmd_dir.get().strip()
        server_path = self.server_dir.get().strip()
        if not steamcmd_path or not server_path:
            messagebox.showwarning(APP_TITLE, "Merci de choisir un dossier SteamCMD et un dossier serveur.")
            return

        self.install_running = True
        self.one_click_btn.configure(state="disabled", text="⏳ Installation en cours...")
        self._reset_checklist()
        self.install_progress.start(12)
        self._install_start_time = time.time()
        self._tick_elapsed_label()
        threading.Thread(target=self._one_click_worker, args=(steamcmd_path, server_path), daemon=True).start()

    def _tick_elapsed_label(self):
        if not self.install_running:
            self.install_elapsed_label.config(text="")
            return
        elapsed = int(time.time() - self._install_start_time)
        mins, secs = divmod(elapsed, 60)
        self.install_elapsed_label.config(text=f"⏱️ Temps écoulé : {mins:02d}:{secs:02d}")
        self.after(1000, self._tick_elapsed_label)

    def _finish_one_click(self, success):
        self.install_running = False
        self.install_progress.stop()
        self.one_click_btn.configure(state="normal", text="🚀  Tout installer en 1 clic")

    def _one_click_worker(self, steamcmd_path, server_path):
        self._log("🚀 Démarrage de l'installation automatique en 1 clic...")

        # 1) Préparation des dossiers
        self._set_checklist_state("prepare", "in_progress")
        for path in (steamcmd_path, server_path):
            if not os.path.isdir(path):
                self._log(f"Le dossier {path} n'existe pas, il va donc être créé.")
                try:
                    os.makedirs(path, exist_ok=True)
                except Exception as e:
                    self._log(f"❌ Impossible de créer le dossier {path} : {e}")
                    self._set_checklist_state("prepare", "failed")
                    self.after(0, lambda: self._finish_one_click(False))
                    return
        self._set_checklist_state("prepare", "done")

        # 2) SteamCMD
        self._set_checklist_state("steamcmd", "in_progress")
        if not self._ensure_steamcmd(steamcmd_path):
            self._set_checklist_state("steamcmd", "failed")
            self._log("❌ Installation arrêtée à SteamCMD. Utilise '🐞 Signaler un problème' si besoin d'aide.")
            self.after(0, lambda: self._finish_one_click(False))
            return
        self._set_checklist_state("steamcmd", "done")

        # 3) Serveur
        self._set_checklist_state("server", "in_progress")
        if not self._ensure_server(steamcmd_path, server_path):
            self._set_checklist_state("server", "failed")
            self._log("❌ Installation arrêtée au Serveur. Utilise '🐞 Signaler un problème' si besoin d'aide.")
            self.after(0, lambda: self._finish_one_click(False))
            return
        self._set_checklist_state("server", "done")

        # 4) Vérification finale
        self._set_checklist_state("verify", "in_progress")
        steamcmd_ok = os.path.isfile(os.path.join(steamcmd_path, "steamcmd.exe"))
        server_exe = os.path.join(server_path, "ArmaReforgerServer.exe")
        server_ok = os.path.isfile(server_exe) and os.path.getsize(server_exe) > 1_000_000

        if steamcmd_ok and server_ok:
            size_mb = folder_size_mb(server_path)
            self._log(f"📦 Taille du dossier serveur : {size_mb} Mo.")
            self._set_checklist_state("verify", "done")
            self._log("🎉 Installation terminée avec succès ! Direction l'étape 2 pour la configuration.")
            self._mark_done(1)
            # Mémorise les dossiers pour que l'app ne redemande PLUS l'installation
            self.after(0, self._save_settings)
            self.after(0, lambda: self._finish_one_click(True))
            self.after(0, lambda: messagebox.showinfo(
                APP_TITLE, "Installation terminée avec succès ! 🎉\nTu peux passer à l'étape 2 (Configuration).",
            ))
        else:
            self._set_checklist_state("verify", "failed")
            self._log("⚠️ Vérification finale échouée : un ou plusieurs fichiers semblent manquants ou incomplets.")
            self.after(0, lambda: self._finish_one_click(False))

    # --- boutons avancés (installation manuelle séparée) --------------------

    def _on_install_steamcmd_only(self):
        path = self.steamcmd_dir.get().strip()
        if not path:
            messagebox.showwarning(APP_TITLE, "Merci de choisir un dossier pour SteamCMD.")
            return
        self.steamcmd_status_label.config(text="Statut SteamCMD : installation en cours...", fg=COLOR_ACCENT_ORANGE)
        threading.Thread(target=self._run_steamcmd_only_worker, args=(path,), daemon=True).start()

    def _run_steamcmd_only_worker(self, path):
        self._ensure_steamcmd(path)

    def _on_install_server_only(self):
        steamcmd_path = self.steamcmd_dir.get().strip()
        server_path = self.server_dir.get().strip()
        if not os.path.isfile(os.path.join(steamcmd_path, "steamcmd.exe")):
            messagebox.showinfo(APP_TITLE, "Installe d'abord SteamCMD (bouton juste à gauche, ou le 1-clic).")
            return
        self.server_status_label.config(text="Statut serveur : installation en cours...", fg=COLOR_ACCENT_ORANGE)
        threading.Thread(target=self._run_server_only_worker, args=(steamcmd_path, server_path), daemon=True).start()

    def _run_server_only_worker(self, steamcmd_path, server_path):
        self._ensure_server(steamcmd_path, server_path)

    # ------------------------------------------------------------------
    # MOTEUR D'INSTALLATION ROBUSTE (utilisé par le 1-clic ET le mode avancé)
    # ------------------------------------------------------------------

    def _run_steamcmd_streaming(self, cmd, cwd=None):
        """Lance une commande SteamCMD, diffuse sa sortie ligne par ligne dans
        le journal, et surveille les silences prolongés pour rassurer
        l'utilisateur pendant les phases longues (téléchargement, extraction,
        validation des fichiers). Ne tue jamais le process pour un simple
        silence : on continue de patienter tant qu'il tourne encore.
        Retourne (code_retour, texte_complet_de_sortie).
        """
        last_output_ts = {"t": time.time()}
        stop_event = threading.Event()
        output_lines = []

        def watchdog():
            reported_steps = 0
            while not stop_event.is_set():
                time.sleep(5)
                elapsed = time.time() - last_output_ts["t"]
                threshold_steps = int(elapsed // WATCHDOG_SILENCE_SECONDS)
                if elapsed > WATCHDOG_SILENCE_SECONDS and threshold_steps > reported_steps:
                    reported_steps = threshold_steps
                    if elapsed > STALL_HARD_LIMIT_SECONDS:
                        self._log(
                            f"⏳ Toujours en cours après {int(elapsed // 60)} min sans nouvelle info. "
                            "C'est long, mais tant que rien n'indique une erreur, on continue de patienter "
                            "(gros téléchargement ou connexion lente). Tu peux annuler et réessayer si besoin."
                        )
                    else:
                        self._log(
                            f"⏳ Installation en cours... (aucune nouvelle info depuis {int(elapsed)}s, "
                            "c'est normal pendant un téléchargement ou une extraction)"
                        )

        watchdog_thread = threading.Thread(target=watchdog, daemon=True)
        watchdog_thread.start()

        returncode = -1
        try:
            proc = subprocess.Popen(
                cmd, cwd=cwd,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace",
                bufsize=1, creationflags=NO_WINDOW_FLAG,
            )
            for line in proc.stdout:
                clean = line.rstrip()
                if clean:
                    output_lines.append(clean)
                    self._log(clean)
                last_output_ts["t"] = time.time()
            proc.wait()
            returncode = proc.returncode
        except Exception as e:
            self._log(f"❌ Erreur lors du lancement de SteamCMD : {e}")
            returncode = -1
        finally:
            stop_event.set()

        return returncode, "\n".join(output_lines)

    def _ensure_steamcmd(self, path):
        """Garantit que SteamCMD est présent ET fonctionnel. Télécharge /
        extrait si besoin, puis vérifie avec des tentatives automatiques.
        Retourne True/False."""
        exe_path = os.path.join(path, "steamcmd.exe")

        if not os.path.isdir(path):
            self._log(f"Le dossier SteamCMD n'existe pas ({path}), il va donc être créé.")
            try:
                os.makedirs(path, exist_ok=True)
            except Exception as e:
                self._log(f"❌ Impossible de créer le dossier : {e}")
                self._set_steamcmd_status("❌ Erreur : dossier impossible à créer", COLOR_ACCENT_RED)
                return False

        if not os.path.isfile(exe_path):
            steamcmd_url = self.steamcmd_url_var.get().strip() or DEFAULT_STEAMCMD_ZIP_URL
            self._log(f"SteamCMD introuvable, téléchargement en cours depuis {steamcmd_url} ...")
            zip_path = os.path.join(path, "steamcmd_tmp.zip")
            try:
                # Téléchargement par blocs avec timeout : évite que l'app
                # reste bloquée pour toujours si la connexion tombe.
                req = urllib.request.Request(steamcmd_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=30) as resp, open(zip_path, "wb") as out:
                    while True:
                        chunk = resp.read(64 * 1024)
                        if not chunk:
                            break
                        out.write(chunk)
            except Exception as e:
                self._log(f"❌ Échec du téléchargement de SteamCMD : {e}")
                self._set_steamcmd_status("❌ Échec du téléchargement (vérifie ta connexion)", COLOR_ACCENT_RED)
                return False

            self._log("Extraction de SteamCMD...")
            try:
                with zipfile.ZipFile(zip_path, "r") as z:
                    z.extractall(path)
            except Exception as e:
                self._log(f"❌ Échec de l'extraction : {e}")
                self._set_steamcmd_status("❌ Échec de l'extraction du zip", COLOR_ACCENT_RED)
                return False
            finally:
                if os.path.isfile(zip_path):
                    try:
                        os.remove(zip_path)
                    except OSError:
                        pass

            if not os.path.isfile(exe_path):
                self._log("❌ steamcmd.exe introuvable après extraction. Vérifie le dossier choisi.")
                self._set_steamcmd_status("❌ steamcmd.exe introuvable après extraction", COLOR_ACCENT_RED)
                return False
        else:
            self._log("SteamCMD est déjà présent, vérification de son bon fonctionnement...")

        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            if attempt == 1:
                self._log("Initialisation de SteamCMD (peut prendre 1 à 2 minutes)...")
            else:
                self._log(f"↻ Nouvelle tentative d'initialisation de SteamCMD ({attempt}/{max_attempts})...")

            returncode, output = self._run_steamcmd_streaming([exe_path, "+quit"], cwd=path)
            still_there = os.path.isfile(exe_path)
            low = output.lower()
            has_real_error = "error!" in low

            if still_there and returncode == 0 and not has_real_error:
                self._log("✅ SteamCMD est installé et fonctionnel.")
                self._set_steamcmd_status("✅ SteamCMD installé et prêt", COLOR_ACCENT_GREEN)
                return True

            if attempt < max_attempts:
                self._log("⚠️ SteamCMD a rencontré un souci pendant son initialisation, nouvel essai dans 4s...")
                time.sleep(4)
            else:
                self._log("❌ SteamCMD ne s'initialise pas correctement après plusieurs tentatives.")
                self._set_steamcmd_status("❌ Échec de l'initialisation après plusieurs tentatives", COLOR_ACCENT_RED)
                return False
        return False

    def _ensure_server(self, steamcmd_path, install_dir):
        """Garantit que le serveur Arma Reforger est installé/à jour, avec
        tentatives automatiques (SteamCMD échoue fréquemment au tout premier
        app_update après une fraîche installation)."""
        steamcmd_exe = os.path.join(steamcmd_path, "steamcmd.exe")
        if not os.path.isfile(steamcmd_exe):
            self._log("❌ SteamCMD introuvable, impossible d'installer le serveur.")
            self._set_server_status("❌ SteamCMD introuvable", COLOR_ACCENT_RED)
            return False

        if not os.path.isdir(install_dir):
            self._log(f"Le dossier serveur n'existe pas ({install_dir}), il va donc être créé.")
            try:
                os.makedirs(install_dir, exist_ok=True)
            except Exception as e:
                self._log(f"❌ Impossible de créer le dossier serveur : {e}")
                self._set_server_status("❌ Erreur : dossier impossible à créer", COLOR_ACCENT_RED)
                return False

        appid = self._get_server_appid()
        beta_branch = self.beta_branch_var.get().strip()

        app_update_args = ["+app_update", appid]
        if beta_branch:
            app_update_args += ["-beta", beta_branch]
            self._log(f"ℹ️ Installation de l'App ID {appid} sur la branche bêta « {beta_branch} ».")
        else:
            self._log(f"ℹ️ Installation de l'App ID {appid} (branche stable).")
        app_update_args.append("validate")

        cmd = [
            steamcmd_exe,
            "+force_install_dir", install_dir,
            "+login", "anonymous",
            *app_update_args,
            "+quit",
        ]
        exe_check = os.path.join(install_dir, "ArmaReforgerServer.exe")

        max_attempts = 3
        known_glitches = ("missing configuration", "state is 0x", "0x602", "0x402")

        for attempt in range(1, max_attempts + 1):
            if attempt == 1:
                self._log("Installation / mise à jour du serveur en cours (patience, plusieurs minutes possibles)...")
            else:
                self._log(f"↻ Nouvelle tentative automatique pour le serveur ({attempt}/{max_attempts})...")

            returncode, output = self._run_steamcmd_streaming(cmd, cwd=None)

            if os.path.isfile(exe_check) and os.path.getsize(exe_check) > 1_000_000:
                self._log("✅ Serveur Arma Reforger installé / mis à jour avec succès.")
                self._set_server_status("✅ Serveur installé", COLOR_ACCENT_GREEN)
                return True

            low = output.lower()
            glitch = any(g in low for g in known_glitches)
            if attempt < max_attempts:
                if glitch:
                    self._log("⚠️ SteamCMD a rencontré un souci temporaire connu au démarrage, nouvel essai dans 4s...")
                else:
                    self._log("⚠️ Le fichier serveur n'est pas encore présent ou semble incomplet, nouvel essai dans 4s...")
                time.sleep(4)
            else:
                self._log("❌ Échec après plusieurs tentatives d'installation du serveur.")
                self._set_server_status("❌ Échec après plusieurs tentatives, réessaie plus tard", COLOR_ACCENT_RED)
                return False
        return False

    def _set_steamcmd_status(self, text, color):
        self.after(0, lambda: self.steamcmd_status_label.config(text=f"Statut SteamCMD : {text}", fg=color))

    def _set_server_status(self, text, color):
        self.after(0, lambda: self.server_status_label.config(text=f"Statut serveur : {text}", fg=color))

    # ------------------------------------------------------------------
    # ETAPE 2 : CONFIGURATION
    # ------------------------------------------------------------------

    def _build_step_config(self, parent):
        frame, card = self._card(
            parent, "Étape 2 — Configurer ton serveur",
            "Donne un nom à ton serveur, choisis un mot de passe si tu veux le "
            "garder privé, et laisse l'assistant détecter tes adresses IP.",
        )

        self._labeled_entry(card, "Nom du serveur :", self.server_name)
        self._labeled_entry(card, "Mot de passe (optionnel) :", self.server_password)
        self._labeled_entry(card, "Mot de passe admin :", self.server_password_admin)

        players_line = tk.Frame(card, bg=COLOR_BG_CARD)
        players_line.pack(fill="x", pady=6)
        tk.Label(
            players_line, text="Joueurs maximum :", font=FONT_NORMAL,
            bg=COLOR_BG_CARD, fg=COLOR_TEXT, width=22, anchor="w",
        ).pack(side="left")
        tk.Spinbox(
            players_line, from_=1, to=128, textvariable=self.max_players,
            width=6, font=FONT_NORMAL, bg="#101620", fg=COLOR_TEXT,
            relief="flat", buttonbackground=COLOR_BG_PANEL,
        ).pack(side="left")

        scenario_line = tk.Frame(card, bg=COLOR_BG_CARD)
        scenario_line.pack(fill="x", pady=6)
        tk.Label(
            scenario_line, text="Scénario :", font=FONT_NORMAL,
            bg=COLOR_BG_CARD, fg=COLOR_TEXT, width=22, anchor="w",
        ).pack(side="left")
        scenario_menu = ttk.Combobox(
            scenario_line, textvariable=self.scenario_choice,
            values=list(SCENARIO_PRESETS.keys()), state="readonly", width=38,
        )
        scenario_menu.pack(side="left")

        self._labeled_entry(card, "ID scénario personnalisé :", self.scenario_custom)
        self._labeled_entry(card, "IP publique :", self.public_ip)
        self._labeled_entry(card, "IP locale :", self.local_ip)

        players_line2 = tk.Frame(card, bg=COLOR_BG_CARD)
        players_line2.pack(fill="x", pady=6)
        tk.Label(
            players_line2, text="Port du serveur :", font=FONT_NORMAL,
            bg=COLOR_BG_CARD, fg=COLOR_TEXT, width=22, anchor="w",
        ).pack(side="left")
        tk.Spinbox(
            players_line2, from_=1, to=65535, textvariable=self.server_port,
            width=8, font=FONT_NORMAL, bg="#101620", fg=COLOR_TEXT,
            relief="flat", buttonbackground=COLOR_BG_PANEL,
        ).pack(side="left")

        btn_row = tk.Frame(card, bg=COLOR_BG_CARD)
        btn_row.pack(anchor="w", pady=(16, 4))
        self._action_button(
            btn_row, "🌐 Détecter mes IP automatiquement", self._on_detect_ips,
            color=COLOR_BG_PANEL, fg=COLOR_TEXT,
        ).pack(side="left", padx=(0, 10))
        self._action_button(
            btn_row, "💾 Générer la configuration", self._on_generate_config,
        ).pack(side="left")

        self.config_status_label = tk.Label(
            card, text="", font=FONT_NORMAL, bg=COLOR_BG_CARD, fg=COLOR_TEXT_DIM,
        )
        self.config_status_label.pack(anchor="w", pady=(10, 0))

        return frame

    def _on_detect_ips(self):
        self.local_ip.set(detect_local_ip())
        threading.Thread(target=self._detect_public_ip_worker, daemon=True).start()

    def _detect_public_ip_worker(self):
        ip = detect_public_ip()
        if ip:
            self.after(0, lambda: self.public_ip.set(ip))
            self._log(f"IP publique détectée : {ip}")
        else:
            self._log("⚠️ Impossible de détecter l'IP publique (vérifie ta connexion internet).")

    def _on_generate_config(self):
        if not self.step_done[1]:
            messagebox.showinfo(APP_TITLE, "Termine d'abord l'installation à l'étape 1 😉")
            return

        scenario_key = self.scenario_choice.get()
        scenario_id = SCENARIO_PRESETS.get(scenario_key, "")
        if not scenario_id:
            scenario_id = self.scenario_custom.get().strip()
        if not scenario_id:
            messagebox.showwarning(
                APP_TITLE, "Choisis un scénario ou saisis un ID de scénario personnalisé.",
            )
            return

        # Lecture sécurisée : un Spinbox vidé par l'utilisateur lèverait un
        # TclError avec .get() → on retombe sur des valeurs par défaut sûres.
        port = self._get_int(self.server_port, 2001)
        max_players = self._get_int(self.max_players, 32)

        config = {
            "region": "fr_fr",
            "bindAddress": "0.0.0.0",
            "bindPort": port,
            "publicAddress": self.public_ip.get().strip() or "0.0.0.0",
            "publicPort": port,
            "a2s": {
                "address": self.local_ip.get().strip() or "127.0.0.1",
                "port": 17777,
            },
            "rcon": {
                "address": self.local_ip.get().strip() or "127.0.0.1",
                "port": 19999,
                "password": "gameTest",
                "permission": "monitor",
                "blacklist": [],
                "whitelist": [],
            },
            "game": {
                "name": self.server_name.get().strip() or "Mon serveur Arma Reforger",
                "password": self.server_password.get().strip(),
                "passwordAdmin": self.server_password_admin.get().strip() or "gameMaster",
                "admins": [],
                "scenarioId": scenario_id,
                "maxPlayers": max_players,
                "visible": True,
                "crossPlatform": True,
                "supportedPlatforms": ["PLATFORM_PC", "PLATFORM_XBL"],
                "gameProperties": {
                    "serverMaxViewDistance": 2500,
                    "serverMinGrassDistance": 50,
                    "networkViewDistance": 1000,
                    "disableThirdPerson": True,
                    "fastValidation": True,
                    "battlEye": True,
                    "VONDisableUI": True,
                    "VONDisableDirectSpeechUI": True,
                },
                "mods": self._build_mods_json(),
            },
            "operating": {
                "lobbyPlayerSynchronise": True,
            },
        }

        server_dir = self.server_dir.get().strip()
        configs_dir = os.path.join(server_dir, "configs")
        try:
            os.makedirs(configs_dir, exist_ok=True)
            config_path = os.path.join(configs_dir, "config.json")
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)

            bat_path = os.path.join(server_dir, "lancer_serveur.bat")
            with open(bat_path, "w", encoding="utf-8") as f:
                f.write(
                    '@echo off\r\n'
                    'ArmaReforgerServer.exe -config ".\\configs\\config.json" '
                    '-profile ArmaReforgerServer -maxFPS 60\r\n'
                    'pause\r\n'
                )

            self._log(f"✅ Configuration générée : {config_path}")
            self._log(f"✅ Script de lancement créé : {bat_path}")
            self.config_status_label.config(text="✅ Configuration enregistrée avec succès", fg=COLOR_ACCENT_GREEN)
            self._mark_done(2)
            self._save_settings()
        except Exception as e:
            self._log(f"❌ Erreur lors de la génération de la configuration : {e}")
            self.config_status_label.config(text=f"❌ Erreur : {e}", fg=COLOR_ACCENT_RED)

    def _build_mods_json(self):
        # Version FREE : la gestion des mods est réservée à la PREMIUM.
        # Le config.json garde une liste "mods" vide (champ attendu par le
        # serveur), que la version PREMIUM sait remplir automatiquement.
        return []

    # ------------------------------------------------------------------
    # ETAPE 3 : MODS — édition manuelle en FREE, gestion 1 clic en PREMIUM
    # ------------------------------------------------------------------

    def _build_step_mods(self, parent):
        frame, card = self._card(
            parent, "Étape 3 — Mods (optionnel)",
            "Si vous voulez, vous pouvez passer à la version PREMIUM pour "
            "gérer facilement vos mods en 1 clic. Sinon, vous pouvez les "
            "ajouter vous-même dans le fichier de configuration ci-dessous.",
        )

        # --- Édition manuelle (version FREE) ---
        tk.Label(
            card, text="✍️  Ajouter mes mods manuellement",
            font=("Segoe UI", 12, "bold"), bg=COLOR_BG_CARD, fg=COLOR_TEXT,
        ).pack(anchor="w", pady=(0, 6))

        tk.Label(
            card,
            text="Ouvre ton config.json et remplis la section \"mods\" avec les Mod ID "
                 "du Workshop Arma Reforger, sur ce modèle :",
            font=FONT_NORMAL, bg=COLOR_BG_CARD, fg=COLOR_TEXT_DIM,
            wraplength=640, justify="left",
        ).pack(anchor="w", pady=(0, 6))

        example = (
            '"mods": [\n'
            '    { "modId": "59674C21AFVOTREMOD", "name": "Nom du mod" },\n'
            '    { "modId": "12345ABCDE67890F", "name": "Un autre mod" }\n'
            ']'
        )
        example_box = tk.Text(
            card, height=5, width=70, bg="#0b0e13", fg=COLOR_TEXT,
            font=("Consolas", 9), bd=0, relief="flat",
        )
        example_box.insert("1.0", example)
        example_box.configure(state="disabled")
        example_box.pack(anchor="w", pady=(0, 10))

        btn_row = tk.Frame(card, bg=COLOR_BG_CARD)
        btn_row.pack(anchor="w", pady=(0, 4))
        self._action_button(
            btn_row, "📝  Ouvrir mon fichier config.json", self._on_open_config_file,
        ).pack(side="left")

        tk.Label(
            card,
            text="💡 Pense à sauvegarder le fichier, puis redémarre le serveur pour "
                 "appliquer les mods. (Attention : régénérer la configuration à "
                 "l'étape 2 remettra la liste \"mods\" à zéro.)",
            font=("Segoe UI", 9), bg=COLOR_BG_CARD, fg=COLOR_TEXT_DIM,
            wraplength=640, justify="left",
        ).pack(anchor="w", pady=(6, 16))

        # --- Encart PREMIUM, sobre ---
        sep = tk.Frame(card, bg=COLOR_LOCKED, height=1)
        sep.pack(fill="x", pady=(0, 12))

        tk.Label(
            card,
            text="⭐ Envie de plus simple ? La version PREMIUM gère tes mods en 1 clic : "
                 "ajout, mise à jour automatique, presets et ordre de chargement.",
            font=FONT_NORMAL, bg=COLOR_BG_CARD, fg=COLOR_TEXT,
            wraplength=640, justify="left",
        ).pack(anchor="w", pady=(0, 8))

        self._action_button(
            card, "⭐  Télécharger la version PREMIUM", self._open_premium_link,
            color=COLOR_ACCENT_ORANGE, fg="#1a1300",
        ).pack(anchor="w")

        tk.Label(
            card, text=f"© {COMPANY_NAME} — {PREMIUM_URL}",
            font=("Segoe UI", 9), bg=COLOR_BG_CARD, fg=COLOR_TEXT_DIM,
        ).pack(anchor="w", pady=(14, 0))

        return frame

    def _on_open_config_file(self):
        """Ouvre le config.json du serveur dans l'éditeur par défaut pour
        que l'utilisateur puisse ajouter ses mods manuellement."""
        server_dir = self.server_dir.get().strip()
        config_path = os.path.join(server_dir, "configs", "config.json")
        if not os.path.isfile(config_path):
            messagebox.showinfo(
                APP_TITLE,
                "Le fichier config.json n'existe pas encore.\n"
                "Génère d'abord ta configuration à l'étape 2 😉",
            )
            return
        try:
            if sys.platform == "win32":
                os.startfile(config_path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", config_path])
            else:
                subprocess.Popen(["xdg-open", config_path])
            self._log(f"📝 Ouverture du fichier de configuration : {config_path}")
        except Exception as e:
            self._log(f"⚠️ Impossible d'ouvrir le fichier automatiquement : {e}")
            messagebox.showwarning(
                APP_TITLE,
                f"Impossible d'ouvrir le fichier automatiquement.\n"
                f"Tu peux l'ouvrir manuellement ici :\n{config_path}",
            )

    def _open_premium_link(self):
        try:
            webbrowser.open(PREMIUM_URL)
            self._log(f"🌐 Ouverture de {PREMIUM_URL} pour télécharger la version PREMIUM...")
        except Exception as e:
            self._log(f"⚠️ Impossible d'ouvrir le navigateur : {e}")

    # ------------------------------------------------------------------
    # ETAPE 4 : LANCER
    # ------------------------------------------------------------------

    def _build_step_launch(self, parent):
        frame, card = self._card(
            parent, "Étape 4 — Lancer ton serveur",
            "Tout est prêt ? Clique sur le gros bouton vert pour démarrer ton "
            "serveur. Tu peux aussi l'arrêter à tout moment.",
        )

        self.launch_status_label = tk.Label(
            card, text="🔴 Serveur arrêté", font=("Segoe UI", 13, "bold"),
            bg=COLOR_BG_CARD, fg=COLOR_ACCENT_RED,
        )
        self.launch_status_label.pack(anchor="w", pady=(0, 16))

        btn_row = tk.Frame(card, bg=COLOR_BG_CARD)
        btn_row.pack(anchor="w")
        self.start_btn = self._action_button(btn_row, "▶️  Démarrer le serveur", self._on_start_server)
        self.start_btn.pack(side="left", padx=(0, 12))
        self.stop_btn = self._action_button(
            btn_row, "⏹️  Arrêter le serveur", self._on_stop_server,
            color=COLOR_ACCENT_RED, fg="#2a0808",
        )
        self.stop_btn.pack(side="left")
        self.stop_btn.configure(state="disabled")

        return frame

    def _on_start_server(self):
        if not self.step_done[2]:
            messagebox.showinfo(APP_TITLE, "Termine d'abord la configuration à l'étape 2 😉")
            return
        if self.server_process is not None:
            messagebox.showinfo(APP_TITLE, "Le serveur est déjà en cours d'exécution.")
            return

        server_dir = self.server_dir.get().strip()
        exe_path = os.path.join(server_dir, "ArmaReforgerServer.exe")
        config_path = os.path.join(server_dir, "configs", "config.json")

        if not os.path.isfile(exe_path):
            messagebox.showerror(APP_TITLE, "ArmaReforgerServer.exe introuvable. Vérifie l'étape 1.")
            return
        if not os.path.isfile(config_path):
            messagebox.showerror(APP_TITLE, "config.json introuvable. Vérifie l'étape 2.")
            return

        cmd = [exe_path, "-config", config_path, "-profile", "ArmaReforgerServer", "-maxFPS", "60"]
        try:
            self.server_process = subprocess.Popen(
                cmd, cwd=server_dir,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace",
                bufsize=1, creationflags=NO_WINDOW_FLAG,
            )
        except Exception as e:
            self._log(f"❌ Impossible de démarrer le serveur : {e}")
            messagebox.showerror(APP_TITLE, f"Impossible de démarrer le serveur :\n{e}")
            return

        self._log("🟢 Serveur démarré.")
        self.launch_status_label.config(text="🟢 Serveur en ligne", fg=COLOR_ACCENT_GREEN)
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self._mark_done(4)

        threading.Thread(target=self._stream_server_output, daemon=True).start()

    def _stream_server_output(self):
        proc = self.server_process
        if proc is None:
            return
        try:
            for line in proc.stdout:
                self._log(line.rstrip())
        except Exception:
            pass
        if self.server_process is proc:
            self.server_process = None
            self._log("🔴 Le serveur s'est arrêté.")
            self.after(0, self._reset_launch_ui)

    def _on_stop_server(self):
        proc = self.server_process
        if proc is None:
            return
        # On retire la référence AVANT d'arrêter, pour que le thread de
        # lecture ne loggue pas un second message "le serveur s'est arrêté".
        self.server_process = None
        try:
            proc.terminate()
            try:
                proc.wait(timeout=8)
            except subprocess.TimeoutExpired:
                self._log("⚠️ Le serveur ne répond pas, arrêt forcé...")
                proc.kill()
                proc.wait(timeout=5)
        except Exception as e:
            self._log(f"⚠️ Erreur en arrêtant le serveur : {e}")
        self._log("⏹️ Serveur arrêté manuellement.")
        self._reset_launch_ui()

    def _reset_launch_ui(self):
        self.launch_status_label.config(text="🔴 Serveur arrêté", fg=COLOR_ACCENT_RED)
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")

    # ------------------------------------------------------------------
    # NAVIGATION / VERROUILLAGE DES ETAPES
    # ------------------------------------------------------------------

    def _go_to_step(self, step):
        if not self._is_unlocked(step):
            messagebox.showinfo(APP_TITLE, "Termine d'abord l'étape précédente pour débloquer celle-ci 🙂")
            return
        self.current_step = step
        for i, fr in self.step_frames.items():
            fr.pack_forget()
        self.step_frames[step].pack(fill="both", expand=True)
        self._refresh_sidebar()

    def _is_unlocked(self, step):
        # Règles explicites : Mods (3) est optionnel et toujours accessible ;
        # Lancer (4) dépend de la Configuration (2), pas des Mods.
        if step == 1:
            return True
        if step == 2:
            return self.step_done.get(1, False)
        if step == 3:
            return True
        if step == 4:
            return self.step_done.get(2, False)
        return False

    def _mark_done(self, step):
        self.step_done[step] = True
        self.after(0, self._refresh_sidebar)

    def _refresh_sidebar(self):
        for i, btn in self.step_buttons.items():
            unlocked = self._is_unlocked(i)
            if i == self.current_step:
                btn.configure(bg=COLOR_ACCENT_GREEN, fg="#08240f", state="normal", cursor="hand2")
            elif unlocked:
                btn.configure(bg=COLOR_BG_CARD, fg=COLOR_TEXT, state="normal", cursor="hand2")
            else:
                btn.configure(bg=COLOR_LOCKED, fg=COLOR_TEXT_DIM, state="normal", cursor="arrow")

    # ------------------------------------------------------------------
    # JOURNAL (LOG) THREAD-SAFE
    # ------------------------------------------------------------------

    def _log(self, text):
        self.log_queue.put(text)

    def _poll_log_queue(self):
        try:
            while True:
                line = self.log_queue.get_nowait()
                self.full_log_history.append(line)
                self.log_text.configure(state="normal")
                self.log_text.insert("end", line + "\n")
                self.log_text.see("end")
                self.log_text.configure(state="disabled")
        except queue.Empty:
            pass
        self.after(150, self._poll_log_queue)

    # ------------------------------------------------------------------
    # SIGNALER UN PROBLEME
    # ------------------------------------------------------------------

    def _on_report_problem(self):
        threading.Thread(target=self._generate_report, daemon=True).start()
        self._log("📄 Génération du rapport de problème en cours...")

    def _generate_report(self):
        lines = [
            f"=== RAPPORT DE PROBLEME - Arma Reforger Server Assistant FREE ({COMPANY_NAME}) ===",
            f"Date : {datetime.datetime.now().isoformat(timespec='seconds')}",
            f"Version du logiciel : {APP_VERSION}",
            f"OS : {platform.platform()}",
            f"Python : {platform.python_version()}",
            f"Dossier SteamCMD : {self.steamcmd_dir.get()}",
            f"Dossier Serveur : {self.server_dir.get()}",
            f"App ID serveur : {self.server_appid_var.get()}",
            f"Branche bêta : {self.beta_branch_var.get() or '(stable)'}",
            f"URL SteamCMD : {self.steamcmd_url_var.get()}",
            f"Fichier de réglages : {SETTINGS_PATH}",
            f"Étapes validées : {self.step_done}",
            "",
            "--- Dernières lignes du journal ---",
        ]
        history = self.full_log_history[-400:]
        lines.extend(history if history else ["(journal vide)"])
        report_text = "\n".join(lines)

        reports_dir = os.path.join(os.path.expanduser("~"), "ArmaReforgerAssistant_Rapports")
        try:
            os.makedirs(reports_dir, exist_ok=True)
            filename = f"rapport_probleme_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            path = os.path.join(reports_dir, filename)
            with open(path, "w", encoding="utf-8") as f:
                f.write(report_text)
        except Exception as e:
            self._log(f"❌ Impossible de créer le rapport : {e}")
            return

        self._log(f"📄 Rapport de problème généré : {path}")
        self.after(0, lambda: self._show_report_ready(path))

    def _show_report_ready(self, path):
        folder = os.path.dirname(path)
        if messagebox.askyesno(
            APP_TITLE,
            f"Un rapport a été créé :\n{path}\n\n"
            "Il contient ton journal récent et des infos système (aucune "
            "donnée personnelle sensible). Tu peux l'envoyer par email, "
            "Discord ou sur le forum du serveur.\n\n"
            "Ouvrir le dossier pour le récupérer ?",
        ):
            try:
                if sys.platform == "win32":
                    os.startfile(folder)
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", folder])
                else:
                    subprocess.Popen(["xdg-open", folder])
            except Exception as e:
                self._log(f"⚠️ Impossible d'ouvrir le dossier automatiquement : {e}")

    # ------------------------------------------------------------------
    # PUBLICITE (version FREE) — toutes les 5 minutes
    # ------------------------------------------------------------------
    # Règles :
    #   - UNE SEULE fenêtre de pub à la fois (jamais 15 empilées) ;
    #   - le compteur de 5 minutes repart de ZÉRO à la FERMETURE de la pub,
    #     pas à son ouverture.

    def _schedule_ad(self):
        # Annule tout minuteur précédent avant d'en programmer un nouveau,
        # pour éviter plusieurs minuteurs en parallèle.
        if self._ad_after_id is not None:
            try:
                self.after_cancel(self._ad_after_id)
            except Exception:
                pass
        self._ad_after_id = self.after(AD_INTERVAL_MS, self._show_ad)

    def _ad_is_open(self):
        return self.ad_window is not None and self.ad_window.winfo_exists()

    def _show_ad(self):
        self._ad_after_id = None

        # Une pub est déjà à l'écran ? On n'en ouvre surtout pas une autre.
        # (Le prochain compte à rebours partira à la fermeture de celle-ci.)
        if self._ad_is_open():
            return

        ad = tk.Toplevel(self)
        self.ad_window = ad
        ad.title("Publicité")
        ad.configure(bg=COLOR_BG_PANEL)
        ad.geometry("440x330")
        ad.resizable(False, False)
        ad.transient(self)
        ad.grab_set()
        ad.protocol("WM_DELETE_WINDOW", lambda: None)

        def close_ad():
            if ad.winfo_exists():
                ad.destroy()
            self.ad_window = None
            # Compteur remis à zéro : les 5 minutes recommencent MAINTENANT.
            self._schedule_ad()

        tk.Label(
            ad, text="⭐ ARMA REFORGER SERVER ASSISTANT PREMIUM ⭐",
            font=("Segoe UI", 13, "bold"), bg=COLOR_BG_PANEL, fg=COLOR_ACCENT_ORANGE,
            wraplength=400, justify="center",
        ).pack(pady=(18, 6))
        tk.Label(
            ad,
            text="Passe à la version PREMIUM pour retirer les publicités,\n"
                 "gérer tes mods en 1 clic et débloquer\n"
                 "les scénarios avancés !",
            font=FONT_NORMAL, bg=COLOR_BG_PANEL, fg=COLOR_TEXT, justify="center",
        ).pack(pady=(0, 10))

        timer_label = tk.Label(ad, text="", font=("Segoe UI", 26, "bold"), bg=COLOR_BG_PANEL, fg=COLOR_TEXT)
        timer_label.pack()

        close_btn = tk.Button(
            ad, text="Fermer", font=FONT_BUTTON, bg=COLOR_LOCKED, fg=COLOR_TEXT_DIM,
            bd=0, relief="flat", padx=16, pady=8, state="disabled",
            command=close_ad,
        )
        close_btn.pack(pady=(12, 8))

        tk.Button(
            ad, text="⭐ Télécharger la version PREMIUM", font=("Segoe UI", 9, "bold"),
            bg=COLOR_ACCENT_ORANGE, fg="#1a1300", bd=0, relief="flat", cursor="hand2",
            command=self._open_premium_link,
        ).pack()

        tk.Button(
            ad, text="⚡ Un vrai serveur hébergé ? Shockbyte, -25 % via notre lien",
            font=("Segoe UI", 9, "bold"), bg=SHOCKBYTE_BLUE, fg="#ffffff",
            bd=0, relief="flat", cursor="hand2", padx=10, pady=6,
            command=self._open_affiliate_link,
        ).pack(pady=(8, 0))

        countdown = {"value": random.randint(5, 10)}

        def tick():
            # La fenêtre a pu être détruite entre-temps : on vérifie.
            if not ad.winfo_exists():
                return
            if countdown["value"] <= 0:
                timer_label.config(text="✅", fg=COLOR_ACCENT_GREEN)
                close_btn.configure(state="normal", bg=COLOR_ACCENT_GREEN, fg="#08240f", cursor="hand2")
                return
            timer_label.config(text=str(countdown["value"]))
            countdown["value"] -= 1
            ad.after(1000, tick)

        tick()

    def _show_pro_popup(self):
        if messagebox.askyesno(
            f"Arma Reforger Server Assistant PREMIUM — {COMPANY_NAME}",
            "La version PREMIUM ajoute :\n\n"
            "• Aucune publicité\n"
            "• Gestion des mods en 1 clic (ajout, mise à jour auto)\n"
            "• Presets de mods et ordre de chargement\n"
            "• Choix avancé des scénarios\n"
            "• Diagnostic des ports / firewall\n"
            "• Profils serveur multiples\n"
            "• Rapports exportables\n\n"
            f"Ouvrir {PREMIUM_URL} pour télécharger la version PREMIUM ?",
        ):
            self._open_premium_link()

    # ------------------------------------------------------------------
    # FERMETURE PROPRE
    # ------------------------------------------------------------------

    def on_close(self):
        if self.server_process is not None:
            if messagebox.askyesno(APP_TITLE, "Le serveur tourne encore. Veux-tu l'arrêter et quitter ?"):
                self._on_stop_server()
            else:
                return
        # Mémorise TOUT (dossiers, config, mods, identifiants Steam) pour
        # que l'application retrouve son état au prochain lancement.
        save_settings(self._collect_settings())
        self.destroy()


def main():
    app = ArmaAssistantFree()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()


if __name__ == "__main__":
    main()
