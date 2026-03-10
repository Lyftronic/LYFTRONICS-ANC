import os
import subprocess
import asyncio
import decky_plugin
from settings import SettingsManager

class Plugin:
    async def _main(self):
        self.settings_dir = os.environ.get("DECKY_PLUGIN_SETTINGS_DIR")
        self.plugin_dir = os.environ.get("DECKY_PLUGIN_DIR")
        self.settings = SettingsManager(name="lyftronics-anc", settings_directory=self.settings_dir)
        self.settings.read()
        decky_plugin.logger.info("lyftronics-anc: Final Production Backend initialized.")

        if self.settings.getSetting("suppression_enabled", False):
            asyncio.create_task(self._delayed_link())

    async def get_suppression_state(self, *args):
        return self.settings.getSetting("suppression_enabled", False)

    async def _delayed_link(self):
        await asyncio.sleep(3)
        env = os.environ.copy()
        env.pop("LD_LIBRARY_PATH", None) 
        decky_user = os.environ.get("DECKY_USER", "deck")
        cmd_prefix = ["sudo", "-u", decky_user, "env", "XDG_RUNTIME_DIR=/run/user/1000"]
        
        internal_fl = "alsa_input.pci-0000_04_00.5-platform-acp5x_mach.0.HiFi__Internal_Mic__source:capture_FL"
        internal_fr = "alsa_input.pci-0000_04_00.5-platform-acp5x_mach.0.HiFi__Internal_Mic__source:capture_FR"
        filter_fl = "capture.rnnoise_source:input_FL"
        filter_fr = "capture.rnnoise_source:input_FR"
        
        try:
            for src, dst in [(internal_fl, filter_fl), (internal_fr, filter_fr)]:
                p_del = await asyncio.create_subprocess_exec(*cmd_prefix, "pw-link", "-d", src, dst, env=env)
                await p_del.wait()
                p_add = await asyncio.create_subprocess_exec(*cmd_prefix, "pw-link", src, dst, env=env)
                await p_add.wait()
            decky_plugin.logger.info("lyftronics-anc: PipeWire routing nodes linked successfully.")
        except Exception as e:
            decky_plugin.logger.error(f"lyftronics-anc: Routing error: {e}")

    async def toggle_suppression(self, enabled: bool):
        self.settings.setSetting("suppression_enabled", enabled)
        self.settings.commit()
        
        decky_home = os.environ.get("DECKY_USER_HOME", "/home/deck")
        decky_user = os.environ.get("DECKY_USER", "deck")
        so_path = os.path.join(self.plugin_dir, "bin/librnnoise_ladspa.so")
        conf_dir = os.path.join(decky_home, ".config/pipewire/pipewire.conf.d/")
        conf_file = os.path.join(conf_dir, "99-input-denoising.conf")
        
        env = os.environ.copy()
        env.pop("LD_LIBRARY_PATH", None)
        cmd_prefix = ["sudo", "-u", decky_user, "env", "XDG_RUNTIME_DIR=/run/user/1000"]

        if enabled:
            os.makedirs(conf_dir, exist_ok=True)
            p_chown_dir = await asyncio.create_subprocess_exec("chown", "-R", f"{decky_user}:{decky_user}", conf_dir)
            await p_chown_dir.wait()
            
            config_content = f"""
context.modules = [
  {{ name = libpipewire-module-filter-chain
    args = {{
      node.description = "Noise Canceling source"
      media.name = "Noise Canceling source"
      filter.graph = {{
        nodes = [
          {{
            type = ladspa
            name = rnnoise
            plugin = "{so_path}"
            label = noise_suppressor_stereo
            control = {{ "VAD Threshold (%)" 50.0 }}
          }}
        ]
      }}
      capture.props = {{
        node.name = "capture.rnnoise_source"
        node.passive = true
      }}
      playback.props = {{
        node.name = "rnnoise_source"
        media.class = Audio/Source
      }}
    }}
  }}
]
"""
            with open(conf_file, "w") as f:
                f.write(config_content.strip())
                
            p_chown_file = await asyncio.create_subprocess_exec("chown", f"{decky_user}:{decky_user}", conf_file)
            await p_chown_file.wait()
            
            p_restart = await asyncio.create_subprocess_exec(*cmd_prefix, "systemctl", "--user", "restart", "pipewire", env=env)
            await p_restart.wait()
            asyncio.create_task(self._delayed_link())
        else:
            if os.path.exists(conf_file):
                os.remove(conf_file)
            p_restart = await asyncio.create_subprocess_exec(*cmd_prefix, "systemctl", "--user", "restart", "pipewire", env=env)
            await p_restart.wait()
            
        return True

    async def _unload(self):
        decky_plugin.logger.info("lyftronics-anc: Backend unloading.")
