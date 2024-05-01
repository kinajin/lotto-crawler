const fs = require("fs");
const path = require("path");
const { LottoStore, WinningInfo } = require("./models");

async function addDataToDatabase() {
  try {
    const winningDataFolder = "lotto_winning_data";
    const storeDataFolder = "lotto_store_data";
    const noSuchStoreFolder = "no_such_store";

    // lotto_winning_data 폴더의 JSON 파일 읽기
    const winningFiles = await fs.promises.readdir(winningDataFolder);

    // lotto_store_data 폴더의 JSON 파일 읽기
    const storeFiles = await fs.promises.readdir(storeDataFolder);

    // 판매점 정보 추가
    for (const file of storeFiles) {
      const filePath = path.join(storeDataFolder, file);
      const data = JSON.parse(await fs.promises.readFile(filePath, "utf-8"));

      for (const store of data.arr) {
        // 판매점 정보 추가
        await LottoStore.create({
          id: store.RTLRID,
          name: store.FIRMNM,
          address: store.BPLCDORODTLADRES,
          phone: store.RTLRSTRTELNO,
          lat: store.LATITUDE,
          lon: store.LONGITUDE,
        });
      }
    }

    // 당첨 정보 추가
    for (const winningInfo of winningFiles) {
      const winningFilePath = path.join(winningDataFolder, winningInfo);
      const winningData = JSON.parse(
        await fs.promises.readFile(winningFilePath, "utf-8"),
      );

      for (const winning of winningData.lotto_stores) {
        const storeExists = await LottoStore.findOne({
          where: { id: winning.store_id },
        });

        if (storeExists) {
          await WinningInfo.create({
            draw_no: winning.drwNo,
            rank: winning.rank,
            category: winning.category || null,
            store_id: winning.store_id,
          });
        } else {
          // store_id가 LottoStores에 존재하지 않는 경우
          const noSuchStoreFilePath = path.join(
            noSuchStoreFolder,
            `no_such_store_${winning.store_id}.json`,
          );

          if (!fs.existsSync(noSuchStoreFolder)) {
            fs.mkdirSync(noSuchStoreFolder);
          }

          fs.writeFileSync(
            noSuchStoreFilePath,
            JSON.stringify(winning, null, 2),
          );
        }
      }
    }

    console.log("데이터베이스에 데이터 추가 완료");
  } catch (error) {
    console.error("데이터 추가 실패:", error);
  }
}

module.exports = { addDataToDatabase };
