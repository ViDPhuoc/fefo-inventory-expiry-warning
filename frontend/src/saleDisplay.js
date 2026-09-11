const collator = new Intl.Collator("vi", {
  numeric: true,
  sensitivity: "base",
});

function productParts(name) {
  const text = name.normalize("NFC").trim();
  const measured = text.match(
    /\s+(\d+(?:[.,]\d+)?)\s*(kg|g|ml|lít|lit|l)\s*$/i,
  );
  if (measured) {
    const value = Number(measured[1].replace(",", "."));
    const unit = measured[2].toLowerCase();
    // Cùng loại: 500 ml phải đứng trước 1 lít, 500 g trước 1 kg.
    return {
      name: text.slice(0, measured.index).replace(/[\s—–-]+$/, ""),
      size: value * (["kg", "lít", "lit", "l"].includes(unit) ? 1000 : 1),
      family: ["kg", "g"].includes(unit) ? "mass" : "volume",
    };
  }
  const pack = text.match(
    /\s*[—–-]\s*(gói nhỏ|gói vừa|gói lớn|hộp\s+\d+\s+(?:phần|chai))$/i,
  );
  if (pack) {
    const value = pack[1].toLowerCase();
    const sizes = { "gói nhỏ": 1, "gói vừa": 2, "gói lớn": 3 };
    return {
      name: text.slice(0, pack.index).trim(),
      family: value.startsWith("gói") ? "pack" : "box",
      size: sizes[value] ?? Number(value.match(/\d+/)[0]),
    };
  }
  return { name: text, family: "other", size: 0 };
}

export function sortSaleProducts(products) {
  // Sắp một bản sao chỉ trong màn hình bán; không đổi danh mục hay thứ tự lô FEFO.
  return [...products].sort((a, b) => {
    const left = productParts(a.ten_sp),
      right = productParts(b.ten_sp);
    return (
      collator.compare(left.name, right.name) ||
      collator.compare(left.family, right.family) ||
      left.size - right.size ||
      collator.compare(a.ten_sp, b.ten_sp) ||
      collator.compare(a.ma_sp, b.ma_sp)
    );
  });
}
