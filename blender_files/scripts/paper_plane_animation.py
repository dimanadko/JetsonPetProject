import bpy
import math
import random
import mathutils  # Import mathutils for vector math operations

# Constants
MAX_DISTANCE = 15  # Maximum distance in meters
MAX_RANDOM_ROTATION = math.radians(20)  # Maximum rotation change in radians per frame
FRAME_START = 1
FRAME_END = 10
OUTPUT_PATH = "/Users/dimanadobko/Programming/Blender/data/paperPlane1/frame_"
FILE_FORMAT = 'PNG'
CAMERA_LENS = 24  # Camera focal length in mm

# Helper function to get or create an object
def get_or_create_object(object_name, creation_operator, **kwargs):
    obj = bpy.data.objects.get(object_name)
    if not obj:
        creation_operator(**kwargs)
        obj = bpy.context.object
        obj.name = object_name
    return obj

# Initialize or create paper plane
paper_plane = get_or_create_object('PaperPlane', bpy.ops.mesh.primitive_plane_add, size=1)

# Initialize or create camera
camera = get_or_create_object('Camera', bpy.ops.object.camera_add, location=(0, 0, 0))
camera.data.lens = CAMERA_LENS  # Set camera properties

# Remove any existing "Track To" constraint
if camera.constraints.get("TrackTo"):
    camera.constraints.remove(camera.constraints["TrackTo"])

# Set animation frame range
scene = bpy.context.scene
scene.frame_start = FRAME_START
scene.frame_end = FRAME_END

# Function to point the camera toward a target
def point_camera_at(camera, target_location):
    # Calculate the direction from the camera to the target
    direction = mathutils.Vector(target_location) - camera.location
    # Compute the rotation to point the camera to the target
    rot_quat = direction.to_track_quat('-Z', 'Y')
    camera.rotation_euler = rot_quat.to_euler()

# Function to apply random position and rotation to the paper plane
def apply_random_transformations(frame):
    random_distance = random.uniform(1, MAX_DISTANCE)
    
    # Use the camera's field of view (FOV) to calculate random positions within the frame
    fov_x = camera.data.angle_x
    fov_y = camera.data.angle_y
    
    
    # Calculate maximum X and Y offsets based on distance and FOV
    max_x_offset = math.tan(fov_x / 2) * random_distance
    max_y_offset = math.tan(fov_y / 2) * random_distance

    # Generate random positions within the FOV range
    new_x = random.uniform(-max_x_offset, max_x_offset)
    new_y = random.uniform(-max_y_offset, max_y_offset)
    new_z = random.uniform(0, 10)  # Random altitude between 0 and 10 meters

    # Random rotations
    new_rotation_pitch = random.uniform(-MAX_RANDOM_ROTATION, MAX_RANDOM_ROTATION)
    new_rotation_yaw = random.uniform(-MAX_RANDOM_ROTATION, MAX_RANDOM_ROTATION)

    # Apply new random position and rotation to the paper plane
    paper_plane.location = (new_x, new_y, new_z)
    paper_plane.rotation_euler = (new_rotation_pitch, paper_plane.rotation_euler.y, new_rotation_yaw)

    # Update camera orientation to point roughly at the paper plane
    point_camera_at(camera, paper_plane.location)

    # Insert keyframes for location and rotation
    paper_plane.keyframe_insert(data_path="location", frame=frame)
    paper_plane.keyframe_insert(data_path="rotation_euler", frame=frame)
    camera.keyframe_insert(data_path="rotation_euler", frame=frame)

# Animate the paper plane
for frame in range(scene.frame_start, scene.frame_end + 1):
    apply_random_transformations(frame)

# Set render settings
scene.render.image_settings.file_format = FILE_FORMAT
scene.render.filepath = OUTPUT_PATH

# Render the animation
bpy.ops.render.render(animation=True)
