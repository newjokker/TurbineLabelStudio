from PIL import Image

def convert_to_ico(input_image_path, output_ico_path, size=(64, 64)):
    """
    将图片转换为 .ico 格式
    :param input_image_path: 输入图片路径
    :param output_ico_path: 输出 .ico 文件路径
    :param size: 输出的图标尺寸，默认为 64x64
    """
    try:
        # 打开图片
        with Image.open(input_image_path) as img:
            img = img.resize(size, Image.Resampling.LANCZOS)
            img.save(output_ico_path, format="ICO")
            print(f"图片已成功转换为 .ico 格式并保存到: {output_ico_path}")
    except Exception as e:
        print(f"转换失败: {e}")



if __name__ == "__main__":
    
    input_image_path = r"/Volumes/Jokker/Code/TurbineLabelStudio/app/static/images/标签.png"
    output_ico_path = r"img.ico"
    
    convert_to_ico(input_image_path, output_ico_path)
    
    
