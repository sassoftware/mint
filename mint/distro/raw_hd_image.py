import os
from conary.lib import util, epdb
import bootable_image

class RawHdImage(bootable_image.BootableImage):
    def write(self):
        try:
            # instantiate the contents that need to go into the image
            self.createFileTree()
            # and instantiate the image itself
            self.createImage()
            self.status('Compressing hard disk image')
            zipfn = self.compressImage(self.outfile)
            imagesList = [(zipfn, 'Raw Hard Disk Image')]
        except:
            if self.imgcfg.debug:
                epdb.post_mortem(sys.exc_info()[2])
            if self.fakeroot:
                util.rmtree(self.fakeroot)
            os.unlink(self.outfile)
            raise
        else:
            if self.fakeroot:
                util.rmtree(self.fakeroot)
            os.unlink(self.outfile)

        return self.moveToFinal(imagesList,
                                os.path.join(self.cfg.finishedPath,
                                             self.project.getHostname(),
                                             str(self.release.getId())))

