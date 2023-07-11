"""
   Copyright (C) 2021  Argyros Argyridis arargyridis at gmail dot com
   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.
   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.
   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


class GDALErrorHandler(object):
    def __init__(self):
        self.last_error = None

    def handler(self, errorLevel: int, errorNo: int, errorMsg: str):
        self.last_error = (errorLevel, errorNo, errorMsg)

    def capture(self):
        """
        Captures the last error and raises a RuntimeError
        :return:
        """
        if self.last_error is not None:
            errorLevel, errorNo, errorMsg = self.last_error
            self.last_error = None
            raise RuntimeError("GDAL Error {0}: {1}".format(errorNo, errorMsg))


def getGDALRasterExtents(inData):
    """
    Returns the extents of a GDAL raster
    :param inData: gdal.Dataset
    :return: gdal.Bounds
    """
    gt = inData.GetGeoTransform()
    bounds = [
        gt[0],
        gt[3] + gt[4] * inData.RasterXSize + gt[5] * inData.RasterYSize,
        gt[0] + gt[1] * inData.RasterXSize + gt[2] * inData.RasterYSize,
        gt[3],
    ]
    return bounds
