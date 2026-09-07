# Hướng dẫn sử dụng `tool.py`

`tool.py` là công cụ giao diện để xem từng ảnh và đánh dấu 120 thuộc tính trong file CSV. Các giá trị thuộc tính được lưu trực tiếp vào file CSV đang mở.

## 1. Yêu cầu cài đặt

- Windows có Python 3.
- Tkinter: thường đã được cài sẵn cùng Python trên Windows.
- Thư viện Pillow:

```powershell
python -m pip install Pillow
```

Kiểm tra Python:

```powershell
python --version
```

## 2. Chạy chương trình

Mở PowerShell hoặc Command Prompt tại thư mục chứa `tool.py`:

```powershell
cd D:\Vkist
python tool.py
```

Nếu máy dùng lệnh `py`, có thể chạy:

```powershell
py tool.py
```

## 3. Chuẩn bị dữ liệu

### File CSV

CSV cần đáp ứng các điều kiện sau:

- Có dòng đầu tiên là tên cột (header).
- Có ít nhất 120 cột thuộc tính.
- Có dữ liệu ảnh ở một cột. Công cụ ưu tiên nhận diện các tên cột sau:
  `image`, `img`, `image_path`, `imagepath`, `path`, `filename`,
  `file_name`, `file`, `image_name`.
- Các cột có hậu tố `_score` được xem là điểm dự đoán và không được tạo thành checkbox.
- Công cụ sử dụng đúng 120 cột thuộc tính đầu tiên sau khi loại cột ảnh và các cột `_score`.
- Giá trị thuộc tính được ghi lại thành `1` (đã chọn) hoặc `0` (chưa chọn).

Ví dụ cấu trúc CSV tối thiểu:

```csv
image,attribute_001,attribute_002,...,attribute_120,attribute_001_score
person_001.jpg,1,0,...,0,0.93
person_002.jpg,0,1,...,1,0.81
```

> Nên sao lưu CSV trước khi sử dụng. Chương trình tự động ghi đè file CSV gốc sau mỗi lần thay đổi checkbox.

### Thư mục ảnh

- Có thể chọn thư mục chứa ảnh và các thư mục con.
- Định dạng được hỗ trợ: `.jpg`, `.jpeg`, `.png`, `.bmp`, `.webp`, `.tif`, `.tiff`.
- Giá trị trong cột ảnh có thể là:
  - đường dẫn tuyệt đối;
  - đường dẫn tương đối so với thư mục ảnh;
  - tên file ảnh.
- Công cụ tìm ảnh theo thứ tự: đường dẫn tuyệt đối, đường dẫn tương đối, đường dẫn trong thư mục đã chọn, rồi đến tên file.
- Nếu không tìm thấy ảnh, thuộc tính vẫn có thể được chỉnh sửa nhưng vùng xem ảnh sẽ báo `Image not found`.

## 4. Quy trình sử dụng

1. Chạy `tool.py`.
2. Nhấn **Load CSV** và chọn file CSV cần gán nhãn.
3. Nhấn **Load Image Folder** và chọn thư mục ảnh tương ứng.
4. Kiểm tra ảnh hiện tại và danh sách 120 thuộc tính.
5. Tích hoặc bỏ tích các checkbox thuộc tính.
6. Dùng **Previous** hoặc **Next** để chuyển ảnh.
7. Nhấn **Save CSV** khi muốn lưu thủ công.
8. Đóng cửa sổ khi hoàn tất.

Mỗi lần checkbox thay đổi, chương trình sẽ cập nhật dòng hiện tại và tự động lưu CSV. Nút **Save CSV** vẫn có thể dùng để lưu thủ công bất cứ lúc nào.

## 5. Các chức năng trên giao diện

### Chọn file

- **Load CSV**: mở file CSV.
- **Load Image Folder**: chọn thư mục chứa ảnh.

### Điều hướng ảnh

- **Previous**: về ảnh trước.
- **Next**: sang ảnh sau.
- Ô **Go to**: nhập số thứ tự ảnh, bắt đầu từ `1`, rồi nhấn **Go** hoặc Enter.
- Nhãn dạng `current / total` cho biết vị trí hiện tại.
- **Checked** cho biết số thuộc tính đang được chọn ở ảnh hiện tại.

Nếu nhập số nhỏ hơn `1` hoặc lớn hơn tổng số ảnh, chương trình sẽ giới hạn về ảnh đầu hoặc ảnh cuối. Nếu nhập không phải số, chương trình sẽ báo lỗi.

### Tìm thuộc tính

Nhập từ khóa vào ô **Search** để chỉ hiển thị các thuộc tính có chứa từ khóa. Nhấn **Clear** để hiển thị lại toàn bộ thuộc tính.

### Lưu

- **Save CSV**: ghi toàn bộ dữ liệu hiện tại vào file CSV đã chọn.
- Khi đóng hoặc chuyển ảnh trong lúc còn thay đổi chưa lưu, chương trình sẽ hỏi có muốn lưu hay không.
- Trạng thái làm việc gần nhất được lưu tự động, gồm file CSV, thư mục ảnh và vị trí ảnh hiện tại.

## 6. Phím tắt

| Phím | Chức năng |
|---|---|
| `Left Arrow` | Ảnh trước |
| `Right Arrow` | Ảnh sau |
| `Ctrl + S` | Lưu CSV |
| `Enter` trong ô Go to | Chuyển đến ảnh đã nhập |

## 7. Vị trí lưu trạng thái phiên

Chương trình lưu trạng thái phiên tại:

```text
%USERPROFILE%\.person_attribute_editor\state.json
```

Xóa file `state.json` nếu muốn chương trình quên file CSV, thư mục ảnh và vị trí ảnh đã dùng trước đó. Việc xóa file trạng thái không xóa dữ liệu trong CSV.

## 8. Xử lý lỗi thường gặp

### `Hãy chọn folder ảnh.`

Hãy chọn thư mục ảnh bằng **Load Image Folder** trước khi tải hoặc tải lại CSV.

### `CSV không có header.`

CSV phải có dòng đầu tiên chứa tên các cột.

### `CSV chỉ tìm thấy ... thuộc tính ... Cần đúng 120.`

Sau khi loại cột ảnh và các cột `_score`, CSV phải còn ít nhất 120 cột thuộc tính. Kiểm tra lại header và thứ tự các cột.

### Ảnh không hiển thị

Kiểm tra:

- thư mục ảnh đã chọn đúng chưa;
- tên file trong CSV có đúng không;
- phần mở rộng ảnh có thuộc danh sách được hỗ trợ không;
- đường dẫn trong CSV có phải đường dẫn tương đối đúng với thư mục đã chọn không.

### Không mở được Pillow

Cài lại thư viện bằng:

```powershell
python -m pip install --upgrade Pillow
```

## 9. Khuyến nghị an toàn dữ liệu

- Sao chép CSV thành một bản dự phòng trước khi bắt đầu.
- Không mở cùng một CSV bằng nhiều phiên bản của công cụ cùng lúc.
- Chờ trạng thái hiển thị `Auto-saved` hoặc `Saved` trước khi tắt chương trình.
- Nếu cần thử nghiệm, hãy làm việc trên bản sao của CSV thay vì file dữ liệu gốc.
