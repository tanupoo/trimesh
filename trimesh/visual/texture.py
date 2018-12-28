import numpy as np

from . import color
from .. import util


class TextureVisuals(object):
    def __init__(self,
                 uv,
                 material=None,
                 image=None):
        """
        Store a material and UV coordinates for a mesh.
        If passed just UV coordinates and a single image it will
        create a SimpleMaterial for the image.
        """
        # should be (n, 2) float, where (n == len(mesh.vertices))
        self.uv = np.asanyarray(uv, dtype=np.float64)

        # if an image is passed create a SimpleMaterial
        if material is None and image is not None:
            self.material = SimpleMaterial(image=image)
        else:
            # may be None
            self.material = material

    def to_color(self):
        """
        Convert textured visuals to a ColorVisuals with vertex
        color calculated from texture.

        Returns
        -----------
        vis : trimesh.visuals.ColorVisuals
          Contains vertex color from texture
        """
        # find the color at each UV coordinate
        colors = self.material.to_color(self.uv)
        # create ColorVisuals from result
        vis = color.ColorVisuals(vertex_colors=colors)
        return vis

    def face_subset(self, face_index):
        pass

    def update_vertices(self, mask):
        """
        Apply a mask to remove or duplicate vertex properties.
        """
        self.uv = self.uv[mask]

    def update_faces(self, mask):
        """
        Apply a mask to remove or duplicate face properties
        """
        pass


class Material(object):
    pass


class SimpleMaterial(Material):
    """
    Hold a single image texture.
    """

    def __init__(self, image):
        self.image = image

    def to_color(self, uv):
        return uv_to_color(uv, self.image)


class PBRMaterial(Material):
    """
    Create a material for physically based rendering as
    specified by GLTF 2.0:
    https://git.io/fhkPZ

    Parameters with `Texture` in them must be PIL.Image objects
    """

    def __init__(self,
                 name=None,
                 emissiveFactor=None,
                 emissiveTexture=None,
                 normalTexture=None,
                 occlusionTexture=None,
                 baseColorTexture=None,
                 baseColorFactor=None,
                 metallicFactor=None,
                 roughnessFactor=None,
                 metallicRoughnessTexture=None):

        # (3,) float
        self.emissiveFactor = emissiveFactor
        # image
        self.emissiveTexture = emissiveTexture
        self.normalTexture = normalTexture
        self.occlusionTexture = occlusionTexture
        self.baseColorTexture = baseColorTexture
        self.metallicRoughnessTexture = metallicRoughnessTexture

    def to_color(self, uv):
        return uv_to_color(uv=uv, image=self.baseColorTexture)


def load(names, resolver):
    """
    Load named textures using a resolver into a PIL image.

    Parameters
    --------------
    names : list of str
      Name of texture files
    resolver : Resolver
      Object to get raw data of texture file

    Returns
    ---------------
    textures : dict
      name : PIL.Image
    """
    # import here for soft dependency
    import PIL
    textures = {}
    for name in names:
        data = resolver.get(name)
        image = PIL.Image.open(util.wrap_as_stream(data))
        textures[name] = image
    return textures


def uv_to_color(uv, image):
    """
    Get the color in a texture image.

    Parameters
    -------------
    uv : (n, 2) float
      UV coordinates on texture image
    image : PIL.Image
      Texture image

    Returns
    ----------
    colors : (n, 4) float
      RGBA color at each of the UV coordinates
    """
    uv = np.asanyarray(uv, dtype=np.float64)

    # get texture image pixel positions of UV coordinates
    x = (uv[:, 0] * (image.width - 1)).round().astype(np.int64)
    y = ((1 - uv[:, 1]) * (image.height - 1)).round().astype(np.int64)

    # wrap to image size in the manner of GL_REPEAT
    x %= image.width
    y %= image.height

    # access colors from pixel locations
    colors = np.asarray(image)[y, x]

    # handle greyscale
    if colors.ndim == 1:
        colors = np.repeat(colors[:, None], 3, axis=1)
    # now ndim == 2
    if colors.shape[1] == 3:
        colors = color.to_rgba(colors)  # rgb -> rgba
    return colors
