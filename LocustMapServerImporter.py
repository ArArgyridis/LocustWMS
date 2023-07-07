"""
   Copyright (C) 2023  Argyros Argyridis arargyridis at gmail dot com
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
from datetime import datetime
from osgeo import gdal, osr
from MapServer import LayerInfo, MapServer
from Utils import *
import os
import sys

gdal.UseExceptions()


class LocustMapServerImporter(object):
    def __init__(self, rootDir: str, url: str = ""):
        """
        rootDir: root directory of the locust data
        url: url of the mapserver
        """
        self._rootDir = rootDir
        self._url = url
        if self._url[-1] != "/":
            self._url += "/"

    def _warpToEPSG(
            self, inFile: str, dstEPSG: int, datePath: str, fl: str
    ) -> gdal.Dataset:
        """
        Warp if destination EPGS code is different from the file's EPSG

        inFile: input file
        dstEPSG: destination epsg

        Return gdal dataset
        """

        try:
            inDt = gdal.Open(inFile)
        except Exception as e:
            print("Error opening the file: ", inFile)
            return None

        proj = osr.SpatialReference(wkt=inDt.GetProjection())
        flEPSG = int(proj.GetAttrValue("AUTHORITY", 1))

        if flEPSG != dstEPSG:
            dstFile = os.path.join(datePath, str(dstEPSG) + "_mapserver_" + fl)
            kwargs = {
                "format": "GTiff",
                "creationOptions": ["TILED=YES", "COMPRESS=LZW"],
                "dstSRS": "EPSG:{0}".format(dstEPSG),
            }
            gdal.Warp(dstFile, inFile, **kwargs)
            ret = gdal.Open(dstFile)
        else:
            ret = inDt

        return ret

    def process(self, dstEPSG: int = 4326) -> None:
        """
        Process the data and upload them to the mapserver
        :param dstEPSG: int, destination EPSG code
        :return: None
        """
        # set error handler
        errorHandler = GDALErrorHandler()
        gdal.PushErrorHandler(errorHandler.handler)
        # get regions
        regions = [
            f
            for f in os.listdir(self._rootDir)
            if os.path.isdir(os.path.join(self._rootDir, f))
        ]
        for region in regions:
            regionPath = os.path.join(self._rootDir, region)

            layerList = []

            # for each date....
            for date in os.listdir(regionPath):
                if date == "archive" or not os.path.isdir(
                        os.path.join(regionPath, date)
                ):
                    continue

                # get all gdal-compliant files from folder
                datePath = os.path.join(regionPath, date)
                for fl in os.listdir(datePath):
                    if os.path.isdir(fl) or fl.endswith("ovr") or "RGB" not in fl:
                        continue
                    inFile = os.path.join(datePath, fl)

                    try:
                        inDt = self._warpToEPSG(
                            inFile, dstEPSG, datePath, fl)

                        # build pyramids
                        overview = inFile + ".ovr"
                        # validate overviews
                        if os.path.isfile(overview):
                            try:
                                overviewDt = gdal.Open(overview)
                                errorHandler.capture()
                            except Exception as e:
                                os.remove(overview)

                        if not os.path.isfile(overview):
                            print("Building pyramids for: ", inDt.GetDescription())
                            gdal.SetConfigOption("COMPRESS_OVERVIEW", "DEFLATE")
                            inDt.BuildOverviews(
                                resampling="AVERAGE", overviewlist=[2, 4, 8, 16, 32, 64]
                            )

                        # append to layerlist
                        layerList.append(
                            LayerInfo(
                                os.path.relpath(inFile, regionPath),
                                os.path.split(inFile)[-1].split(".")[0],
                                "EPSG:{0}".format(dstEPSG),
                                inDt.RasterXSize,
                                inDt.RasterYSize,
                                getGDALRasterExtents(inDt),
                                datetime.strptime(date, "%Y%m%d").isoformat()[0:10],
                            )
                        )

                    except Exception as e:
                        print("Error: ", e)

            # sort files....
            layerList.sort(key=lambda x: x.date, reverse=True)
            latestDate = layerList[0].date
            stop = False
            i = 0
            while not stop:
                if layerList[i].date == latestDate:
                    layerList[i].layerName += "_LATEST"
                    i += 1
                else:
                    stop = True

            # run mapserver file generator
            obj = MapServer(
                layerList,
                self._url + region,
                os.path.join(regionPath, "mapserver.map"),
                "Locust WMS Service",
            )
            obj.process()


def main():
    """
    Main function
    :return: None
    """

    assert (
            len(sys.argv) < 3
    ), "usage: python LocustMapServerImporter.py root_dir root_wms_url"

    obj = LocustMapServerImporter(sys.argv[1], sys.argv[2])
    obj.process()


if __name__ == "__main__":
    """
    Main entry point
    :argument
    :argument https://locust.wms.cgls.dev/greeness
    """
    main()
