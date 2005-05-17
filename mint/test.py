import mint_server
import config

cfg = config.MintConfig()
cfg.read("../mint.cfg")
ms = mint_server.MintServer(cfg)

ms.newProject("Foo Project", "foo", "The foo project is a test")
