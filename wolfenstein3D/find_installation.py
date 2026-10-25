

import os
import platform
import shutil


class WolfInstallationFinder:
    def __init__(self):
        self.sysname = platform.system().lower()
        self.sysproc = platform.processor()

        self.gamefiles_path_steam = os.path.join(
            "steamapps", "common", "Wolfenstein 3D", "base")
        self.package_maps_path = os.path.join(
            __package__.split('.')[0], "assets", "maps")

    def find_installation(self):
        steam_files = self.search_steam()
        if not steam_files:
            return False
        self.copy_maps(steam_files)
        return True

    def copy_maps(self, sources):
        for src in sources:
            shutil.copy(src, self.package_maps_path)

    def search_steam(self):
        if self.get_steam_path() is None:
            return False
        abs_gamefiles_path = os.path.join(
            self.steam_path, self.gamefiles_path_steam)
        if not os.path.exists(abs_gamefiles_path):
            return False
        gamemaps6 = os.path.join(
            abs_gamefiles_path, "GAMEMAPS.WL6")
        maphead6 = os.path.join(
            abs_gamefiles_path, "MAPHEAD.WL6")

        if not (os.path.exists(gamemaps6) or os.path.exists(maphead6)):
            return False
        return gamemaps6, maphead6

    def get_steam_path(self):
        self.steam_path = getattr(self, f"get_steam_path_{self.sysname}")()
        return self.steam_path

    def get_steam_path_windows(self):
        import winreg
        """Retrieves the main Steam installation path from the Registry."""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Valve\Steam")
            steam_path, _ = winreg.QueryValueEx(key, "SteamPath")
            return os.path.normpath(steam_path)
        except FileNotFoundError:
            return None

    def get_steam_path_linux(self):
        possible_dirs = ["~/.local/share/Steam/steamapps/common/",
                         "~/.steam/steam/steamapps/common/",
                         "~/.var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/common/",
                         "~/.var/app/com.valvesoftware.Steam/.steam/steam/steamapps/common/",
                         "~/snap/steam/common/.local/share/Steam/steamapps/common/"]
        for dir_ in possible_dirs:
            if os.path.exists(dir_):
                return dir_
        return None

    def get_steam_path_macos(self):
        possible_dirs = ["~/Library/Application Support/Steam",]
        for dir_ in possible_dirs:
            if os.path.exists(dir_):
                return dir_
        return None

    def get_steam_path_darwin(self):
        possible_dirs = ["~/Library/Application Support/Steam",]
        for dir_ in possible_dirs:
            if os.path.exists(dir_):
                return dir_
        return None
