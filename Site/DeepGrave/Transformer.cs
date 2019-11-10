using NumSharp;
using OpenCvSharp;
using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.IO;
using System.Net;
using Tensorflow;
using System.Linq; 

namespace DeepGrave
{
    public class Transformer
    {
        private static NDArray loadImage(string fileName)
        {
            Tensor jpegFile = Binding.tf.read_file(fileName, "file");
            jpegFile = Binding.tf.image.decode_jpeg(jpegFile, name: "jpeg_reader");
            jpegFile = Binding.tf.cast(jpegFile, Binding.tf.float32);
            jpegFile = Binding.tf.expand_dims(jpegFile, 0);
            jpegFile = Binding.tf.divide(jpegFile, new float[] { 127.5f });
            jpegFile = Binding.tf.subtract(jpegFile, new float[] { 1.0f });

            Session sess = new Session();
            return sess.run(jpegFile);
        }

        /// <summary>
        /// Resize the image to the specified width and height.
        /// </summary>
        /// <param name="image">The image to resize.</param>
        /// <param name="width">The width to resize to.</param>
        /// <param name="height">The height to resize to.</param>
        /// <returns>The resized image.</returns>
        private static Bitmap resizeImage(Image image, int width, int height)
        {
            Console.WriteLine($"Width: {image.HorizontalResolution}, Height: {image.VerticalResolution}"); 
            var destRect = new Rectangle(0, 0, width, height);
            var destImage = new Bitmap(width, height);

            destImage.SetResolution(96, 96);

            using (var graphics = Graphics.FromImage(destImage))
            {
                graphics.CompositingMode = CompositingMode.SourceCopy;
                graphics.CompositingQuality = CompositingQuality.HighQuality;
                graphics.InterpolationMode = InterpolationMode.HighQualityBicubic;
                graphics.SmoothingMode = SmoothingMode.HighQuality;
                graphics.PixelOffsetMode = PixelOffsetMode.HighQuality;

                using (var wrapMode = new ImageAttributes())
                {
                    wrapMode.SetWrapMode(WrapMode.TileFlipXY);
                    graphics.DrawImage(image, destRect, 0, 0, image.Width, image.Height, GraphicsUnit.Pixel, wrapMode);
                }
            }

            return destImage;
        }

        public static Bitmap FindFace(Bitmap inputImage, string openCvHaarClassifierFile)
        {
            Bitmap ret = null;
            using (var haarCascade = new CascadeClassifier(openCvHaarClassifierFile))
            {
                // Load target image
                using (MemoryStream mem = new MemoryStream())
                {
                    inputImage.Save(mem, ImageFormat.Jpeg);
                    mem.Seek(0, SeekOrigin.Begin);

                    Mat gray = Mat.FromStream(mem, ImreadModes.Grayscale);

                    // Detect faces
                    Rect[] faces = haarCascade.DetectMultiScale(
                                        gray, 1.08, 2, HaarDetectionType.ScaleImage, new OpenCvSharp.Size(30, 30));

                    if (faces.Length > 0)
                    {
                        Rect face = faces.Where(n => n.Width * n.Height == faces.Max(m => m.Width * m.Height)).FirstOrDefault();

                        if (face != null)
                        {
                            // find the center. 
                            OpenCvSharp.Point diffVector = (face.BottomRight - face.TopLeft);
                            int middleX = (int)Math.Round(face.TopLeft.X + diffVector.X / 2.0f);
                            int middleY = (int)Math.Round(face.TopLeft.Y + diffVector.Y / 2.0f);

                            // take the rectangle they gave us, and make a square out of the smallest dimension. 
                            // this is guaranteed to not go out of the bounds. Then add 10% (or until we hit up against the 
                            // edges of the picture) so that we don't overcrop. 

                            // 1. add some percentage to the largeste dimension. this adds a buffer 
                            // around the image since the training data often included stuff around the image. 
                            int newRadius = (int)Math.Round(Math.Max(face.Width, face.Height) * .75f);

                            // 2. Check each cardinal dimension to make sure we don't go over. If we do, resize. 
                            // Then continue onto the next one. 
                            if (middleX - newRadius < 0) // left
                            {
                                newRadius = middleX;
                            }
                            if (middleX + newRadius > inputImage.Width) // right
                            {
                                newRadius = inputImage.Width - middleX;
                            }
                            if (middleY + newRadius > inputImage.Height) // down
                            {
                                newRadius = inputImage.Height - middleY;
                            }
                            if (middleY - newRadius < 0)
                            {
                                newRadius = middleY;
                            }

                            int newLeft = middleX - newRadius;
                            int newTop = middleY - newRadius;
                            int newLength = newRadius * 2;
                            using (Bitmap cloned = inputImage.Clone(new Rectangle(newLeft, newTop, newLength, newLength), inputImage.PixelFormat))
                            {
                                ret = resizeImage(cloned, 256, 256);
                            }
                        }
                    }
                    return ret;
                }
            }
        }

        public Bitmap Transform(Bitmap inputImage, string pathToFrozenFile, string openCvHaarClassifierFile)
        {
            if(inputImage.Width > 512)
            {
                float fraction = 512 / (inputImage.Width * 1.0f);
                inputImage = resizeImage(inputImage,
                    (int)Math.Round(inputImage.Width * fraction),
                   (int)Math.Round(inputImage.Height * fraction));

                //inputImage.Save("C:/users/ben/desktop/turd.bmp", ImageFormat.Bmp); 
            }

            Bitmap ret = null;

            // temporary file name. will get deleted at the end. 
            string tempName = Guid.NewGuid().ToString().Replace("-", "");

            Bitmap face = FindFace(inputImage, openCvHaarClassifierFile); 

            if(face != null)
            {
                inputImage = face; 
            }

            // what's the aspect ratio? we will remember this and reset it later. d
            float ratio = inputImage.Height / (inputImage.Width * 1.0f);
            using (Bitmap resizedImage = resizeImage(inputImage, 256, 256))
            {
                // save to disk. I don't know how to laod this 
                // into TF's libraries without it coming from disk. 
                Console.Write($"writing to {tempName} in directory {Directory.GetCurrentDirectory()}"); 
                resizedImage.Save(tempName, ImageFormat.Jpeg);
            }

            try
            {
                Graph g = new Graph();
                // import the pb file. 
                if (g.Import(pathToFrozenFile))
                {
                    Session session = new Session(g);

                    Operation input = null, output = null;
                    // find the entrypoint and exitpoint of the graph. 
                    foreach (Operation op in g)
                    {
                        if (op.name == "real_A_and_B_images")
                        {
                            input = op;
                        }
                        else if (op.name == "generatorA2B/Tanh")
                        {
                            output = op;
                        }
                    }

                    if (input != null && output != null)
                    {
                        // load the image from disk (see above)
                        NDArray image = loadImage(tempName);

                        // run the network. 
                        NDArray outputValue = session.run(output.outputs[0],
                            new FeedItem(input.outputs[0], image));


                        // transform into a bitmap
                        using (Bitmap bmp = new Bitmap(256, 256))
                        {
                            for (int y = 0; y < bmp.Height; y++)
                            {
                                for (int x = 0; x < bmp.Width; x++)
                                {
                                    float r = (outputValue.GetSingle(0, y, x, 0) + 1) * 127.5f;
                                    float gr = (outputValue.GetSingle(0, y, x, 1) + 1) * 127.5f;
                                    float b = (outputValue.GetSingle(0, y, x, 2) + 1) * 127.5f;

                                    bmp.SetPixel(x, y, Color.FromArgb((int)r, (int)gr, (int)b));
                                }
                            }

                            // resize the image. 
                            ret = resizeImage(bmp, 256, (int)(256 * ratio));
                        }
                    }
                }
            }
            finally
            {
                System.IO.File.Delete(tempName);
            }

            return ret;
        }
    }
}
