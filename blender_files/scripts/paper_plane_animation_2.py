import bpy
import math
import random
import mathutils  # Import mathutils for vector math operations

print('Watch out!')  # will print a message to the console

# Constants
MAX_DISTANCE = 2  # Maximum distance in meters
MAX_RANDOM_ROTATION = math.radians(20)  # Maximum rotation change in radians per frame
FRAME_START = 1
FRAME_END = 50
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

fov_alpha = camera.data.angle_x
fov_beta = camera.data.angle_y

# print('fov_alpha, fov_beta', fov_alpha, fov_beta)

# Remove any existing "Track To" constraint
if camera.constraints.get("TrackTo"):
    camera.constraints.remove(camera.constraints["TrackTo"])

# Set animation frame range
scene = bpy.context.scene
scene.frame_start = FRAME_START
scene.frame_end = FRAME_END

def get_new_coordinates_for_plane(phi, theta, distance):
    alpha_random = random.uniform(-fov_alpha/2, fov_alpha/2)

    print('alpha_random in degrees', math.degrees(alpha_random))

    new_distance = abs(distance / math.cos(alpha_random))
    # print("sin(alpha_random)", math.sin(alpha_random))

    new_angle_theta = theta + alpha_random

    x = new_distance * math.sin(phi) * math.cos(new_angle_theta)
    y = new_distance * math.sin(phi) * math.sin(new_angle_theta)

    z = new_distance * math.cos(phi)


    print("New dist vs old", new_distance, distance)
    return x, y, z



# Function to point the camera toward a target
def point_camera_at(camera, target_location):
    # Calculate the direction from the camera to the target
    direction = mathutils.Vector(target_location) - camera.location
    # Compute the rotation to point the camera to the target
    rot_quat = direction.to_track_quat('-Z', 'Y')
    camera.rotation_euler = rot_quat.to_euler()

# Function to apply random position and rotation to the paper plane
def apply_random_transformations(frame):
    # Generate a random distance from the camera that is less than or equal to MAX_DISTANCE
    distance = random.uniform(1, MAX_DISTANCE)  # Start from 1 to avoid zero distance

    # Generate a random direction for the paper plane within a sphere
    theta = random.uniform(0, 2 * math.pi)  # Angle in the XY-plane
    phi = random.uniform(-math.pi/2, math.pi/2)  # Angle from the Z-axis

    # Convert spherical coordinates to Cartesian coordinates
    x = distance * math.sin(phi) * math.cos(theta)
    y = distance * math.sin(phi) * math.sin(theta)
    z = distance * math.cos(phi)  # Positive Z to keep it above ground

    # Set the new random location for the paper plane
    new_location = (x, y, z)
    paper_plane.location = new_location

    # Log the new location
    # print(f"Frame {frame}: New Location - X: {x:.2f}, Y: {y:.2f}, Z: {z:.2f}")

    

    # Randomly change the rotation of the paper plane within the maximum rotation range
    new_rotation = (
        random.uniform(-MAX_RANDOM_ROTATION, MAX_RANDOM_ROTATION),
        random.uniform(-MAX_RANDOM_ROTATION, MAX_RANDOM_ROTATION),
        random.uniform(-MAX_RANDOM_ROTATION, MAX_RANDOM_ROTATION)
    )

    paper_plane.rotation_euler = new_rotation


    # Log the new rotation
    # print(f"Fr`ame {frame}: New Rotation - X: {math.degrees(new_rotation[0]):.2f}, Y: {math.degrees(new_rotation[1]):.2f}, Z: {math.degrees(new_rotation[2]):.2f}")

        
    # Update camera orientation to point at the new location of the paper plane
    point_camera_at(camera, paper_plane.location)

    x_new, y_new, z_new = get_new_coordinates_for_plane(phi, theta, distance)
    # print(f"Frame {frame}: New New Location - X: {x_new:.2f}, Y: {y_new:.2f}, Z: {z_new:.2f}")

    paper_plane.location = ( x_new, y_new, z_new)

    # based on the camera's field of view (FOV) calculate possible random positions within the frame and apply them to the paper plane


    # Insert keyframes for location and rotation
    paper_plane.keyframe_insert(data_path="location", frame=frame)
    paper_plane.keyframe_insert(data_path="rotation_euler", frame=frame)
    camera.keyframe_insert(data_path="rotation_euler", frame=frame)


# Animate the paper plane
for frame in range(scene.frame_start, scene.frame_end + 1):
    
    fov_alpha = camera.data.angle_x
    fov_beta = camera.data.angle_y

    # print('fov_alpha, fov_beta', fov_alpha, fov_beta)
    
    apply_random_transformations(frame)

# Set render settings
scene.render.image_settings.file_format = FILE_FORMAT
scene.render.filepath = OUTPUT_PATH

# Render the animation
bpy.ops.render.render(animation=True)
