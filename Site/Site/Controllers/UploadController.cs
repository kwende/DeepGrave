using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using NumSharp;
using Tensorflow;

namespace Site.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class UploadController : Controller
    {
        [HttpPost]
        public IActionResult UploadFile(IFormCollection form)
        {
            // get the file, save it to a stream. 
            IFormFile file = this.Request.Form.Files.First();
            Stream stream = file.OpenReadStream();
            byte[] fileBuffer = new byte[file.Length];
            stream.Read(fileBuffer, 0, fileBuffer.Length);

            using (Bitmap bmp = new Bitmap(new MemoryStream(fileBuffer)))
            {
                // do some deep shit
                DeepGrave.Transformer tf = new DeepGrave.Transformer();
                using (Image newImage = tf.Transform(bmp, "frozen32.pb", "haar.xml"))
                {
                    // serve that bitch. 
                    using (MemoryStream mout = new MemoryStream())
                    {
                        newImage.Save(mout, ImageFormat.Jpeg);
                        mout.Seek(0, SeekOrigin.Begin);
                        if(this.Request.Query.ContainsKey("dobinary"))
                        {
                            return File(mout.ToArray(), "image/jpeg"); 
                        }
                        else
                        {
                            return Json(new
                            {
                                data = "data:image/jpeg;base64," + Convert.ToBase64String(mout.ToArray())
                            });
                        }
                    }
                }
            }
        }
    }
}