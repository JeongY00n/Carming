import {CompositeScreenProps} from '@react-navigation/native';
import {NativeStackScreenProps} from '@react-navigation/native-stack';
import {useEffect, useState} from 'react';
import {StyleSheet, Dimensions} from 'react-native';
import {useTheme} from 'react-native-paper';
import {SafeAreaView} from 'react-native-safe-area-context';
import styled from 'styled-components';
import {
  useGetCurrentCarPositionQuery,
  useGetGlobalPathQuery,
  useSetDriveStartStatusMutation,
  useSetIsDestinationMutation,
} from '../apis/journeyApi';
import {CarCallInfoCard, CustomButton, CustomMapView} from '../components';
import {iconPlace} from '../components/MapMarker';
import {L3_TotalJourneyStackParamList} from '../navigations/L3_TotalJourneyStackNavigator';
import {L4_JourneyStackParamList} from '../navigations/L4_JourneyStackNavigator';
import {calcArrivalTime, coordinateToIconPlace} from '../utils';
import {useCheckIsDestinationQuery} from '../apis/journeyApi';
import {useDispatch} from 'react-redux';
import {setCurrentIdx} from '../redux/slices/journeySlice';

export type CarCallScreenProps = CompositeScreenProps<
  NativeStackScreenProps<L4_JourneyStackParamList, 'CarCall'>,
  NativeStackScreenProps<L3_TotalJourneyStackParamList>
>;

const CarCallScreen: React.FC<CarCallScreenProps> = ({navigation, route}) => {
  const theme = useTheme();
  const dispatch = useDispatch();
  const {start: startCoordinate, end: endCoordinate} = route.params;

  const startPlace = coordinateToIconPlace('map-marker', startCoordinate);
  const endPlace = coordinateToIconPlace('hail', endCoordinate);

  const [buttonAbled, setButtonAbled] = useState<boolean>(false);
  const [currentCarPlace, setCurrentCarPlace] = useState<iconPlace>(
    coordinateToIconPlace('taxi', startCoordinate),
  );
  const [arrivalTime, setArrivalTime] = useState<{
    hour: number;
    minute: number;
  }>(calcArrivalTime(startCoordinate, endCoordinate));

  const {data: currentCarCoordinate} = useGetCurrentCarPositionQuery(
    undefined,
    {
      pollingInterval: navigation.isFocused() ? 1000 : undefined,
    },
  );
  const {data: globalPath} = useGetGlobalPathQuery();
  const {data: isDestination} = useCheckIsDestinationQuery(undefined, {
    pollingInterval: navigation.isFocused() ? 1000 : undefined,
  });
  const [setDriveStartStatus] = useSetDriveStartStatusMutation();
  const [setIsDestination] = useSetIsDestinationMutation();

  useEffect(() => {
    if (currentCarCoordinate !== undefined) {
      const {latitude: lat, longitude: lon} = currentCarCoordinate;
      setCurrentCarPlace({...currentCarPlace, lat, lon});
      setArrivalTime(calcArrivalTime(currentCarCoordinate, endCoordinate));
    }
  }, [currentCarCoordinate]);

  useEffect(() => {
    if (globalPath !== undefined) {
    }
  }, [globalPath]);

  useEffect(() => {
    if (isDestination !== undefined) {
      setButtonAbled(isDestination);
    }
  }, [isDestination]);

  const completeBoardBtnPressed = () => {
    setDriveStartStatus(1);
    setIsDestination(0);
    dispatch(setCurrentIdx(1));
    navigation.replace('CarMove');
  };

  return (
    <StyledSafeAreaView>
      <CarCallInfoCard
        statusText={
          isDestination ? '카밍카가 도착했어요.' : '카밍카가 출발했어요.'
        }
        infoText={
          isDestination
            ? '탑승완료 버튼을 눌러주세요.'
            : `${arrivalTime.hour !== 0 ? `${arrivalTime.hour}시간` : ''} ${
                arrivalTime.hour === 0 && arrivalTime.minute === 0
                  ? '곧'
                  : `${arrivalTime.minute}분 내로`
              } 도착할 예정이에요.`
        }
        imageActive={!isDestination}
      />
      <CustomMapView
        places={[startPlace, endPlace, currentCarPlace]}
        viewStyle={{flex: 1}}
        latitudeOffset={0}
        routeCoordinates={globalPath}
      />
      <CustomButton
        text={'차량 탑승 완료'}
        onPress={() => completeBoardBtnPressed()}
        disabled={!buttonAbled}
        buttonStyle={{
          ...styles.buttonStyle,
          backgroundColor: buttonAbled
            ? theme.colors.secondary
            : theme.colors.surfaceDisabled,
        }}
        textStyle={styles.buttonText}
      />
    </StyledSafeAreaView>
  );
};

const styles = StyleSheet.create({
  buttonStyle: {
    width: 200,
    padding: 14,
    height: 50,
    borderRadius: 30,
    position: 'absolute',
    bottom: 20,
    left: Dimensions.get('window').width * 0.5 - 100,
  },
  buttonText: {
    fontWeight: 'bold',
    fontSize: 14,
    textAlign: 'center',
  },
});

const StyledSafeAreaView = styled(SafeAreaView)`
  flex: 1;
  justify-content: center;
`;

export default CarCallScreen;
