#!/usr/bin/env python3
"""
Zombie Animation Exporter
Combines zombie character with animation files
"""
import os
import subprocess
import sys

class ZombieExporter:
    def __init__(self):
        self.zombie_dir = "/Users/khosilmurod/Desktop/plant/zombie"
        self.output_dir = "/Users/khosilmurod/Desktop/plant/web_assets"
        self.gltf_file = os.path.join(self.output_dir, "zombie.gltf")
        self.blender_path = "/Applications/Blender.app/Contents/MacOS/Blender"
        
        # Animation files mapping - SWAPPED for correct sequence
        self.animations = {
            "die": "Dying.fbx",
            "idle": "Hip Hop Dancing.fbx",  # Hip hop dance is the main idle loop
            "idle_breathing": "Zombie Idle.fbx",  # Zombie idle is the "breathing" variant
            "swipe": "Receiving An Uppercut.fbx"  # Uppercut for swipe
        }

    def find_files(self):
        """Find animation files"""
        print("✅ Checking zombie files:")
        
        # Check animation files  
        found_animations = {}
        for anim_name, filename in self.animations.items():
            anim_path = os.path.join(self.zombie_dir, filename)
            if os.path.exists(anim_path):
                found_animations[anim_name] = anim_path
                print(f"   {anim_name}: {filename}")
            else:
                print(f"⚠️  Animation not found: {filename}")
        
        if not found_animations:
            print("❌ No animation files found")
            return False
            
        self.found_animations = found_animations
        return True

    def create_export_script(self):
        """Create Blender Python script for export"""
        
        animations_dict = "{\n"
        for name, path in self.found_animations.items():
            animations_dict += f'    "{name}": r"{path}",\n'
        animations_dict += "}"

        script = f'''
import bpy
import os

print("🧟 Setting up Zombie export...")

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Animation paths
animations = {animations_dict}

print("📁 Loading zombie animations...")

# Import first animation as base (includes mesh and armature)
first_anim = list(animations.items())[0]
base_name, base_path = first_anim
print(f"📥 Importing base from: {{os.path.basename(base_path)}}")
bpy.ops.import_scene.fbx(filepath=base_path)

# Find the base armature and mesh
base_armature = None
base_mesh = None

for obj in bpy.context.scene.objects:
    if obj.type == 'ARMATURE':
        base_armature = obj
        base_armature.name = "Zombie_Armature"
        print(f"✅ Found armature: {{base_armature.name}}")
    elif obj.type == 'MESH':
        base_mesh = obj
        base_mesh.name = "Zombie_Mesh"
        print(f"✅ Found mesh: {{base_mesh.name}} ({{len(base_mesh.data.vertices)}} vertices)")

if not base_armature:
    print("❌ No armature found")
    exit(1)

# Rename the first action
if base_armature.animation_data and base_armature.animation_data.action:
    action = base_armature.animation_data.action
    action.name = f"{{base_name}}_animation"
    print(f"✅ Renamed base action to: {{action.name}}")

# Import remaining animations
for anim_name, fbx_path in list(animations.items())[1:]:
    if fbx_path and os.path.exists(fbx_path):
        print(f"📥 Importing {{anim_name}}: {{os.path.basename(fbx_path)}}")
        
        # Store current objects
        objects_before = set(bpy.context.scene.objects)
        
        # Import animation FBX
        bpy.ops.import_scene.fbx(filepath=fbx_path)
        
        # Find new objects
        objects_after = set(bpy.context.scene.objects)
        new_objects = objects_after - objects_before
        
        # Process new armature and copy animations
        for obj in new_objects:
            if obj.type == 'ARMATURE':
                # Copy animation action
                if obj.animation_data and obj.animation_data.action:
                    action = obj.animation_data.action
                    action.name = f"{{anim_name}}_animation"
                    print(f"   ✅ Renamed to: {{action.name}}")
                
                # Remove the temporary armature
                bpy.data.objects.remove(obj, do_unlink=True)
            elif obj.type == 'MESH':
                # Remove duplicate meshes
                bpy.data.objects.remove(obj, do_unlink=True)

# Report final actions
print("🎭 Final animations:")
action_count = 0
for action in bpy.data.actions:
    print(f"   {{action.name}} ({{action.frame_range[1] - action.frame_range[0]:.0f}} frames)")
    action_count += 1

print(f"✅ Total actions: {{action_count}}")

# Select base armature and mesh for export
print("📦 Selecting objects for export:")
bpy.ops.object.select_all(action='DESELECT')
base_armature.select_set(True)
if base_mesh:
    base_mesh.select_set(True)
    print(f"   ✅ Mesh: {{base_mesh.name}} ({{len(base_mesh.data.vertices)}} vertices)")
bpy.context.view_layer.objects.active = base_armature
print(f"   ✅ Armature: {{base_armature.name}}")

# Create output directory
output_dir = r"{self.output_dir}"
os.makedirs(output_dir, exist_ok=True)

# Export to glTF
gltf_path = r"{self.gltf_file}"
print(f"🚀 Exporting to: {{gltf_path}}")

bpy.ops.export_scene.gltf(
    filepath=gltf_path,
    export_format='GLTF_SEPARATE',
    use_selection=True,
    export_animations=True,
    export_frame_range=False,
    export_force_sampling=True,
    export_nla_strips=False,
    export_def_bones=True,
    export_optimize_animation_size=False
)

print("✅ Export complete!")
print(f"📁 Files saved to: {{output_dir}}")
'''
        return script

    def run_blender_export(self):
        """Run Blender with the export script"""
        print(f"🎨 Using Blender: {self.blender_path}")
        print("🚀 Running Blender export...")
        
        script = self.create_export_script()
        
        # Write script to a temporary file
        script_path = os.path.join(self.output_dir, "temp_zombie_export.py")
        os.makedirs(self.output_dir, exist_ok=True)
        with open(script_path, 'w') as f:
            f.write(script)
        
        try:
            result = subprocess.run([
                self.blender_path,
                "--background",
                "--python", script_path
            ], capture_output=True, text=True, timeout=120)
            
            # Print Blender output with proper formatting
            for line in result.stdout.split('\n'):
                if any(marker in line for marker in ['🧟', '📁', '📥', '✅', '🎬', '🎭', '📦', '🚀', '❌']):
                    print(f"   {line}")
            
            if result.stderr and "WARNING" not in result.stderr:
                print(f"⚠️  Blender warnings:\n{result.stderr}")
                
            # Clean up temporary script
            if os.path.exists(script_path):
                os.remove(script_path)
                
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print("❌ Blender export timed out")
            if os.path.exists(script_path):
                os.remove(script_path)
            return False
        except Exception as e:
            print(f"❌ Error running Blender: {e}")
            if os.path.exists(script_path):
                os.remove(script_path)
            return False

    def verify_export(self):
        """Verify the exported files"""
        if not os.path.exists(self.gltf_file):
            print(f"❌ Export failed - no glTF file found")
            return False
            
        # List created files
        files = []
        for file in os.listdir(self.output_dir):
            if file.startswith("zombie."):
                files.append(file)
                
        print(f"✅ Export successful!")
        print(f"📁 Created {len(files)} files:")
        for file in sorted(files):
            file_path = os.path.join(self.output_dir, file)
            size = os.path.getsize(file_path)
            print(f"   - {file} ({size:,} bytes)")
            
        return True

    def export(self):
        """Main export function"""
        print("🧟 Zombie Animation Exporter")
        print("=" * 50)
        
        if not self.find_files():
            return False
            
        if not self.run_blender_export():
            return False
            
        if not self.verify_export():
            return False
            
        print("\n🎉 Zombie ready for web viewer!")
        print("Animation mappings:")
        print("  - Die: Dying")
        print("  - Idle: Zombie Idle")
        print("  - Idle Breathing: Hip Hop Dancing 💃")
        print("  - Swipe: Receiving An Uppercut 🥊")
        return True

def main():
    exporter = ZombieExporter()
    success = exporter.export()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
