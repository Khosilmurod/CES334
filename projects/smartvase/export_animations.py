#!/usr/bin/env python3
"""
NPC Animation Exporter - Version 2
Combines base character model with animation files
"""
import os
import subprocess
import sys

class NPCExporter:
    def __init__(self):
        self.npc_dir = "/Users/khosilmurod/Desktop/npc"
        self.output_dir = "/Users/khosilmurod/Desktop/plant/web_assets"
        self.gltf_file = os.path.join(self.output_dir, "npc.gltf")
        self.blender_path = "/Applications/Blender.app/Contents/MacOS/Blender"
        
        # Base model and animation files
        self.base_model = "Mutant.fbx"
        self.animations = {
            "idle": "mutant idle.fbx",
            "idle_breathing": "mutant breathing idle.fbx",
            "die": "mutant dying.fbx", 
            "swipe": "mutant swiping.fbx"
        }

    def find_files(self):
        """Find the base model and animation files"""
        print("✅ Found files:")
        
        # Check base model
        base_path = os.path.join(self.npc_dir, self.base_model)
        if not os.path.exists(base_path):
            print(f"❌ Base model not found: {self.base_model}")
            return False
        print(f"   base: {self.base_model}")
        
        # Check animation files  
        found_animations = {}
        for anim_name, filename in self.animations.items():
            anim_path = os.path.join(self.npc_dir, filename)
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
        base_path = os.path.join(self.npc_dir, self.base_model)
        
        animations_dict = "{\n"
        for name, path in self.found_animations.items():
            animations_dict += f'    "{name}": r"{path}",\n'
        animations_dict += "}"

        script = f'''
import bpy
import os

print("🎨 Setting up NPC export...")

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Animation paths
animations = {animations_dict}

print("📁 Loading base character model...")

# Import base character model with mesh
base_model_path = r"{base_path}"
print(f"📥 Importing base model: {{os.path.basename(base_model_path)}}")
bpy.ops.import_scene.fbx(filepath=base_model_path)

# Find the base armature and mesh
base_armature = None
base_mesh = None

for obj in bpy.context.scene.objects:
    if obj.type == 'ARMATURE':
        base_armature = obj
        base_armature.name = "NPC_Armature"
        print(f"✅ Found base armature: {{base_armature.name}}")
    elif obj.type == 'MESH':
        base_mesh = obj
        base_mesh.name = "NPC_Mesh"
        print(f"✅ Found base mesh: {{base_mesh.name}} ({{len(base_mesh.data.vertices)}} vertices)")

if not base_armature or not base_mesh:
    print("❌ Base model missing armature or mesh")
    exit(1)

print("📁 Loading animation files...")

# Import animations and merge into base armature
for anim_name, fbx_path in animations.items():
    if fbx_path and os.path.exists(fbx_path):
        print(f"📥 Importing {{anim_name}}: {{os.path.basename(fbx_path)}}")
        
        # Store current objects
        objects_before = set(bpy.context.scene.objects)
        
        # Import animation FBX
        bpy.ops.import_scene.fbx(filepath=fbx_path)
        
        # Find new objects
        objects_after = set(bpy.context.scene.objects)
        new_objects = objects_after - objects_before
        
        # Process new armature and merge animations
        for obj in new_objects:
            if obj.type == 'ARMATURE':
                # Copy animations from this armature to base armature
                if obj.animation_data and obj.animation_data.action:
                    action = obj.animation_data.action
                    print(f"   🎬 Found action: {{action.name}}")
                    
                    # Rename action based on animation type
                    if anim_name == "idle":
                        action.name = "idle_animation"
                    elif anim_name == "die":
                        action.name = "die_animation"
                    elif anim_name == "swipe":
                        action.name = "swipe_animation"
                    
                    print(f"   ✅ Renamed to: {{action.name}}")
                
                # Remove the temporary armature
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
base_mesh.select_set(True)
bpy.context.view_layer.objects.active = base_armature

print(f"   ✅ Armature: {{base_armature.name}}")
print(f"   ✅ Mesh: {{base_mesh.name}} ({{len(base_mesh.data.vertices)}} vertices)")

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
        script_path = os.path.join(self.output_dir, "temp_export_script.py")
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
            for line in result.stdout.split('\\n'):
                if any(marker in line for marker in ['🎨', '📁', '📥', '✅', '🎬', '🎭', '📦', '🚀', '❌']):
                    print(f"   {line}")
            
            if result.stderr and "WARNING" not in result.stderr:
                print(f"⚠️  Blender warnings:\\n{result.stderr}")
                
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
            if file.startswith("npc."):
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
        print("🌱 NPC Animation Exporter v2")
        print("=" * 50)
        
        if not self.find_files():
            return False
            
        if not self.run_blender_export():
            return False
            
        if not self.verify_export():
            return False
            
        print("\\n🎉 Ready to start web viewer!")
        print("Next: Run the web viewer to see your NPC with mesh and animations")
        return True

def main():
    exporter = NPCExporter()
    success = exporter.export()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()